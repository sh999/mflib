# MIT License
#
# Copyright (c) 2023 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#



from random import randint
import os.path
import itertools

def check_owl_prerequisites(slice):
    """
    Checks whether remote nodes have PTP and Docker required for running OWL.

    :param slice:
    :type slice: fablib.Slice
    """
    
    nodes = slice.get_nodes()
    
    for node in nodes:
        if node.get_name() != "meas-node":
            print(f"\n***** On {node.get_name()}...")
            print("\n***** Is github reachable?")
            node.execute("git clone https://github.com/fabric-testbed/teaching-materials.git")
            node.execute("ls -l")
            node.execute("rm -rf teaching-materials")
            print("\n***** Is PTP is enabled?")
            node.execute("ps -ef | grep phc2sys")
            print("\n*****Is Docker installed?")
            node.execute("docker --help | head")


def nodes_ip_addrs(slice):
    """
    List the node experiment IP address for all nodes. This is particularly useful
    when using a (Measurement Framework) meas-node + meas_net since the returned dictionary
    will NOT include the meas_net addresses.  It assumes each node has only one experiment 
    interface.
    
    :param slice:
    :type slice: fablib.Slice
    :return: list of IP addresses
    :rtype: List[str]
    """
    
    # Assumes there is only 1 experimenter's IP
    nodes = slice.get_nodes()
    node_ips = {}
    for node in nodes: 
        # The following line excludes management net interface
        interfaces = node.get_interfaces()
        exp_network_ips = []
        for interface in interfaces:
            network = interface.toDict()['network']
            if 'l3_meas_net' not in network:
                node_ips[node.get_name()] = str(interface.get_ip_addr())
        #         exp_network_ips.append(interface.get_ip_addr())
        # node_ips[node.get_name()] = exp_network_ips
    
    return node_ips


def pull_owl_docker_image(node, image_name):
    """
    Pull Docker OWL image to remote node.

    :param node: remote node
    :type node: fablib.Node
    """        
    print(f"\n Pulling OWL docker image on {node.get_name()}")
    node.execute(f"sudo docker pull {image_name}")
        

def start_owl_sender(slice, src_node, dst_node, img_name, probe_freq=1, duration=600, no_ptp=False, src_addr=None, dst_addr=None):
    """
    Start OWL sender inside a Docker container on a remote node by running udp_sender.py.  
    Docker container name will be in the form of "owl-sender_10.0.0.1-10.0.1.1"
    
    :param slice:
    :type slice: fablib.Slice
    :param src_node: source (sender) node
    :type src_node: fablib.Node
    :param dst_node: destination (capturer) node
    :type dst_node: fablib.Node
    :param img_name: Docker image name
    :type img_name: str
    :param prob_freq: (default=1) interval (sec) at which probe packets are sent
    :type prob_freq: int
    :param duration: (default=600) how long (sec) to run OWL
    :type duratino: int
    :param no_ptp: (default=False) Set this to True only when testing the functionalities on non-PTP node
    :type no_ptp: bool
    :src_addr: (default=None) Specify source IP address only if source node has more than 1 experiment interface
    :type src_addr: str 
    :dst_addr: (default=None) Specify destination IP address only if dest node has more than 1 experiment interface
    :type dst_addr: str 
    
    """

    # pull owl image fron DockerHub
    #stdout, stderr = node.execute(f'sudo docker pull {img_name}')
    
    # Figure out the node based on the IP address given
    ip_list = nodes_ip_addrs(slice)
    src_ip = ip_list[src_node.get_name()] if not src_addr else src_addr 
    dst_ip = ip_list[dst_node.get_name()] if not dst_addr else dst_addr
    
    
    # Start seq_n
    num = randint(1, 1000)
    
    # Container will be removed
    src_cmd = f'sudo docker run -d \
                --rm \
                --network="host"  \
                --pid="host" \
                --privileged \
                --name owl-sender_{src_ip}_{dst_ip} \
                {img_name}  sock_ops/udp_sender.py  \
                --ptp-so-file "/MeasurementFramework/user_services/owl/owl/sock_ops/time_ops/ptp_time.so" \
                --dest-ip {dst_ip} --dest-port 5005 --frequency {probe_freq} \
                --seq-n {num} --duration {duration}'

    if no_ptp:
        # Just use Python time.time_ns() for timestamping
        src_cmd += '--sys-clock'

    stdout, stderr = src_node.execute(src_cmd)    
    



def start_owl_capturer(slice, dst_node, img_name, outfile=None, duration = 600, delete_previous=True, dst_addr=None):
    """
    Start OWL capturer inside a Docker container on a remote node by running udp_capturer.py.  
    One container instance per node (sometimes serving multiple source nodes).
    Docker container name will be in the form of "owl-capturer_10.0.0.1"

    :param slice:
    :type slice: fablib.Slice
    :param dst_node: destination (capturer) node
    :type src_node: fablib.Node
    :param img_name: Docker image name
    :type img_name: str
    :param outfile: /path/on/remote/node/to/ouput.pcap (if None, `/home/rocky/owl-output/{dst_ip}.pcap`)
    :type outfile: str
    :param duration: (default=600) how long (sec) to run OWL
    :type duration: int
    :param delete_previous: (default=True) whether to delete all existing pcap files from previous runs
    :type delete_previous: bool
    :dst_addr: (default=None) Specify destination IP address only if dest node has more than 1 experiment interface
    :type dst_addr: str 
    """
    
    
    # Figure out the node based on the IP address given
    ip_list = nodes_ip_addrs(slice)
    dst_ip = ip_list[dst_node.get_name()] if not dst_addr else dst_addr    
    
    
    # check if it is already running
    stdout, stderr = dst_node.execute("sudo docker ps --format '{{.Names}}'")
    if f'owl-capturer_{dst_ip}' in stdout:
        print(f"capturer already running on {dst_node.get_name()}")
        return
    
    # create outfile dir
    if not outfile:
        outfile = f'/home/rocky/owl-output/{dst_ip}.pcap'
        
    dir_name = os.path.dirname(outfile)
    file_name = os.path.basename(outfile)
    
    stdout, stderr = dst_node.execute(f'mkdir -p {dir_name}')
    
    # delete previous results if desired
    if delete_previous:
        stdout, stderr = dst_node.execute(f'rm -f {dir_name}/*.pcap')
        
    
    # Container will be removed
    dst_cmd = f'sudo docker run -d \
    --rm \
    --mount type=bind,source={dir_name},target=/owl_output \
    --network="host"  \
    --pid="host" \
    --privileged \
    --name owl-capturer_{dst_ip} \
    {img_name}  sock_ops/udp_capturer.py \
    --ip {dst_ip} \
    --port 5005 \
    --outfile /owl_output/{file_name} \
    --duration {duration}'

    #print(dst_cmd)
    stdout, stderr = dst_node.execute(dst_cmd) 
    
    
    
def start_owl(slice, src_node, dst_node, img_name, probe_freq=1, no_ptp=False, outfile=None, 
              duration = 600, delete_previous_output=True, src_addr=None, dst_addr=None):
    """
    Start OWL on a given link defined by source and destination nodes.

    :param slice:
    :type slice: fablib.Slice
    :param src_node: source (sender) node
    :type src_node: fablib.Node
    :param dst_node: destination (capturer) node
    :type dst_node: fablib.Node
    :param img_name: Docker image name
    :type img_name: str
    :param prob_freq: (default=1) interval (sec) at which probe packets are sent
    :type prob_freq: int
    :param duration: (default=600) how long (sec) to run OWL
    :type duration: int
    :param no_ptp: (default=False) Set this to True only when testing the functionalities on non-PTP node
    :type no_ptp: bool
    :param outfile: /path/on/remote/node/to/ouput.pcap (if None, `/home/rocky/owl-output/{dst_ip}.pcap`)
    :type outfile: str
    :param delete_previous: (default=True) whether to delete all existing pcap files from previous runs
    :type delete_previous: bool
    :src_addr: (default=None) Specify source IP address only if source node has more than 1 experiment interface
    :type src_addr: str 
    :dst_addr: (default=None) Specify destination IP address only if dest node has more than 1 experiment interface
    :type dst_addr: str 
    """

    print(f'Staring sender on {src_node.get_name()}')
    start_owl_sender(slice,
                     src_node,
                     dst_node,
                     img_name,
                     probe_freq=probe_freq,
                     duration=duration,
                     src_addr=src_addr,
                     dst_addr=dst_addr)

    print(f'Staring capturer on {dst_node.get_name()}')
    start_owl_capturer(slice,
                       dst_node,
                       img_name,
                       outfile=outfile,
                       duration=duration,
                       delete_previous=delete_previous_output,
                       dst_addr=dst_addr)

    


def start_owl_all(slice, img_name, probe_freq=1, outfile=None, duration=600, delete_previous=True):
    """
    Start OWL on all possible combination of nodes in the slice. It asssumes there is only 1 
    experimenter's network interface on each node (exclu. meas-net interface)

    :param slice:
    :type slice: fablib.Slice
    :param src_node: source (sender) node
    :type src_node: fablib.Node
    :param dst_node: destination (capturer) node
    :type dst_node: fablib.Node
    :param img_name: Docker image name
    :type img_name: str
    :param prob_freq: (default=1) interval (sec) at which probe packets are sent
    :type prob_freq: int
    :param outfile: /path/on/remote/node/to/ouput.pcap (if None, `/home/rocky/owl-output/{dst_ip}.pcap`)
    :type outfile: str
    :param duration: (default=600) how long (sec) to run OWL
    :type duration: int
    :param no_ptp: (default=False) Set this to True only when testing the functionalities on non-PTP node
    :type no_ptp: bool
    :param delete_previous: (default=True) whether to delete all existing pcap files from previous runs
    :type delete_previous: bool
    """
    
    nodes = slice.get_nodes()
    nodes = [node for node in nodes if node.get_name() != 'meas-node']
    products = list(itertools.product(nodes, nodes))
    all_links = [link for link in products if link[0]!=link[1]]


    for link in all_links:

        src_node = link[0]
        dst_node = link[1]
        print(f"{src_node.get_name()} --> {dst_node.get_name()}")
              
        print('Staring sender')
        start_owl_sender(slice,
                         src_node,
                         dst_node,
                         img_name,
                         probe_freq=probe_freq,
                         duration=duration)
        
        print(f'Staring capturer')
        start_owl_capturer(slice,
                           dst_node,
                           img_name,
                           outfile=outfile,
                           duration=duration,
                           delete_previous=delete_previous)

def stop_owl_sender(slice, src_node, dst_node, src_addr=None, dst_addr=None):
    """
    Stops OWL sender container if there is one or more running on a remote node.

    :param slice:
    :type slice: fablib.Slice
    :param src_node: source (sender) node
    :type src_node: fablib.Node
    :param dst_node: destination (capturer) node
    :type dst_node: fablib.Node
    :src_addr: (default=None) Specify source IP address only if source node has more than 1 experiment interface
    :type src_addr: str 
    :dst_addr: (default=None) Specify destination IP address only if dest node has more than 1 experiment interface
    :type dst_addr: str 
    """
    
    # Figure out the node based on the IP address given
    ip_list = nodes_ip_addrs(slice)
    src_ip = ip_list[src_node.get_name()] if not src_addr else src_addr 
    dst_ip = ip_list[dst_node.get_name()] if not dst_addr else dst_addr
    
    src_node.execute(f'sudo docker stop owl-sender_{src_ip}-{dst_ip}')
    
    
    
def stop_owl_capturer(slice, dst_node, dst_addr=None):
    """
    Stops OWL capturer container if there is one running on a remote node.

    :param slice:
    :type slice: fablib.Slice
    :param dst_node: destination (capturer) node
    :type dst_node: fablib.Node
    :dst_addr: (default=None) Specify destination IP address only if dest node has more than 1 experiment interface
    :type dst_addr: str 
    """
    
    # Figure out the node based on the IP address given
    ip_list = nodes_ip_addrs(slice)
    dst_ip = ip_list[dst_node.get_name()] if not dst_addr else dst_addr
    
    dst_node.execute(f'sudo docker stop owl-capturer_{dst_ip}')

    
def stop_owl_all(slice):
    """
    Stop ALL running instances of OWL containers on all nodes in the slice
    
    :param slice:
    :type slice: fablib.Slice
    """
    
    nodes = slice.get_nodes()
    nodes = [node for node in nodes if node.get_name() != 'meas-node']
    for node in nodes:
        node.execute('hostname')
        node.execute('sudo docker container stop $(sudo docker container ls -q --filter name=owl-*)')

def check_owl_all(slice):
    """
    Prints the list of all running containers on all nodes in the slice.
    
    :param slice:
    :type slice: fablib.Slice
    """
    
    nodes = slice.get_nodes()
    nodes = [node for node in nodes if node.get_name() != 'meas-node']
    
    for node in nodes:
        node.execute('hostname')
        stdout, stderr = node.execute('sudo docker ps -a')
        
        
def download_output(node, local_out_dir):
    """
    Download the contents of owl output directory on a remote node to 
    the local owl output directory.

    :param node: remote node
    :type node: fablib.Node
    :param local_out_dir: /path/to/local/dir/under/which/pcaps/will/be/saved
    :type local_out_dir: str
    """


    local_dir = os.path.join(local_out_dir, node.get_name())

    try:
        os.makedirs(local_dir)
    except(FileExistsError):
        print("directory exists.")

    # get the list of files on the remote dir  
    remote_out_dir = '/home/rocky/owl-output'
    
    stdout, stderr = node.execute(f"sudo ls {remote_out_dir}")
    files = [x for x in stdout.split('\n') if x!='']

    if not files:
        print("no output files found")
        return

    else:
        # This is necessary due to permissions
        node.execute('mkdir -p /tmp/owl_copy')

        for file_name in files:
            local_path = os.path.join(local_dir, file_name)
            remote_path = os.path.join(remote_out_dir, file_name)

            remote_tmp_path = os.path.join('/tmp/owl_copy', file_name)

            node.execute(f"sudo cp {remote_path} {remote_tmp_path}")
            node.execute(f"sudo chmod 0664 {remote_tmp_path}")
            node.download_file(local_path, remote_tmp_path)
            print(f"Downloaded {remote_path} from {node.get_name()} to {local_path}")

            node.execute(f"sudo rm {remote_tmp_path}") 
            
