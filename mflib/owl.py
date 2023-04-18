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

import os
import json
from pathlib import Path
from configparser import ConfigParser

from fabrictestbed_extensions.fablib.fablib import fablib

class Owl():
    """
    Parent class
    """
    
    def __init__(self, local_owl_dir, remote_out_dir, remote_conf_dir = None):
        """
        Constructor.
        
        :param local_owl_dir: owl directory path under which conf and output dirs 
                              will be created.
        :type local_owl_dir: str
        :param remote_out_dir: directory on a remote host where output (.pcap)
                               files will be saved.
        :type remote_out_dir: str
        :param remote_conf_dir: directory on a remote host where config files should
                                be uploaded.
        :type remote_conf_dir: str
        """
        
        self.local_out_dir = os.path.join(local_owl_dir, "output")
        self.local_conf_dir = os.path.join(local_owl_dir, "conf")
        self.remote_out_dir = remote_out_dir
        self.remote_conf_dir = remote_conf_dir

        # Go ahead and create a local owl directory for output and conf files
        self.create_local_service_dirs()
        
        
    def create_local_service_dirs(self):
        """
        Create local directories where OWL config and output files will be kept
        """
        try:
            os.makedirs(self.local_conf_dir)
        except(FileExistsError):
            print(f"{self.local_conf_dir} directory already exists. Check the contents.")

        try:
            os.makedirs(self.local_out_dir)
        except(FileExistsError):
            print(f"{self.local_out_dir} directory already exists. Check the contents.")


    ########## output data management methods ##########
    
    def create_remote_out_dir(self, node):
        """
        Creates owl output directory on a remote node.
        
        :param node: remote node
        :type node: fablib.Node
        """
        
        stdout, stderr = node.execute(f"mkdir -p {self.remote_out_dir}")
        
        
    def list_remote_output(self, node):
        """
        List the contents of owl output directory on a remote node.
        
        :param node: remote node
        :type node: fablib.Node
        """
        
        stdout, stderr = node.execute(f"sudo ls -lh {self.remote_out_dir}")
    
    
    def download_output(self, node):
        """
        Download the contents of owl output directory on a remote node to 
        the local owl output directory.
        
        :param node: remote node
        :type node: fablib.Node
        """


        local_dir = os.path.join(self.local_out_dir, node.get_name())

        try:
            os.makedirs(local_dir)
        except(FileExistsError):
            print("directory exists.")

        # get the list of files on the remote dir           
        stdout, stderr = node.execute(f"sudo ls {self.remote_out_dir}")
        files = [x for x in stdout.split('\n') if x!='']

        if not files:
            print("no output files found")
            return

        else:
            node.execute('mkdir -p /tmp/owl_copy')

            for file_name in files:
                local_path = os.path.join(local_dir, file_name)
                remote_path = os.path.join(self.remote_out_dir, file_name)

                remote_tmp_path = os.path.join('/tmp/owl_copy', file_name)

                node.execute(f"sudo cp {remote_path} {remote_tmp_path}")
                node.execute(f"sudo chmod 0664 {remote_tmp_path}")
                node.download_file(local_path, remote_tmp_path)
                print(f"Downloaded {remote_path} from {node.get_name()} to {local_path}")

                node.execute(f"sudo rm {remote_tmp_path}")             
            
            
    def delete_remote_output(self, node):
        """
        Deletes the contents of owl output directory on a remote node.
        
        :param node: remote node
        :type node: fablib.Node
        """
        
        stdout, stderr = node.execute(f"sudo rm -r {self.remote_out_dir}")


    ########## conf file methods ###########
    
    def create_remote_conf_dir(self, node):
        """
        Creates owl conf directory on a remote node.
        
        :param node: remote node
        :type node: fablib.Node
        """
        stdout, stderr = node.execute(f"mkdir -p {self.remote_conf_dir}")
        
        
    def generate_local_config(self,
                              send_int=0.5,
                              port=5005,
                              cap_mode="save",
                              pcap_int=120):

        """
        Generate local copy of owl.conf file (to serve as a master copy)
        
        :param send_int: interval at which probe packets will be sent (in seconds)
        :type send_int: float
        :param port: port to be used by OWL
        :type port: int
        :param cap_mode: capture mode for OWL. Currently only "save" is supported.
        :type cap_mode: str
        :param pcap_int: time interval (sec) at which tcpdump will start a new pcap file.
        :type pcap_int: int
        """
        
        config = ConfigParser()
        config.optionxform = str

        config['GENERAL'] = {}
        config['GENERAL']['UdpPort'] = str(port)

        config['sender'] = {}
        config['sender']['SendInterval'] = str(send_int)

        config['receiver'] = {}
        config['receiver']['CaptureMode'] = cap_mode
        config['receiver']['PcapInterval'] = str(pcap_int)

        local_conf_file = os.path.join(self.local_conf_dir, "owl.conf")

        with open (local_conf_file, 'w') as configfile:
            config.write(configfile)

            
    def generate_local_links_file(self, links):
        """
        Create a local copy of links.json file.

        :param links: list of endpoint pairs [('src_ip', 'dst_ip')]
        :type links: [(str, str)] 
        """

        links_list = []
        for link in links:
            endpoints = {}
            endpoints['src'] = link[0]
            endpoints['dst'] = link[1]
            links_list.append(endpoints)

        tmp_d = {}
        tmp_d["links"] = links_list

        jsonified_links = json.dumps(tmp_d, indent=4)
        local_links_path = os.path.join(self.local_conf_dir, "links.json")

        with open(local_links_path, 'w') as json_out:
            json_out.write(jsonified_links)
            
   
    def get_local_service_file_paths(self):
        """
        Get paths for owl.conf and links.json files.
        
        :return: owl.conf path, links.json path
        :rtype: [str, str]
        """

        return [os.path.join(self.local_conf_dir, "owl.conf"),
                os.path.join(self.local_conf_dir, "links.json")]
        
        
        
    def print_local_service_files(self):
        """
        Prints local copies of owl.conf and links.json.
        """

        files = self.get_local_service_file_paths()

        for file in files:
            try:
                print(file)
                f = open(file, 'r')
                print(f.read())
                f.close()
            except:
                print(f"{file} not found")

                
    ########### 
    
        
    @staticmethod
    def list_experiment_ip_addrs(node):
        """
        Get a list of IPs for a given remote node, excluding the interfaces used for
        management and MF networks

        :param node: remote node 
        :type node: fablib.Node
        :return: list of IP addresses
        :rtype: List[str]
        """

        # The following line excludes management net interface
        interfaces = node.get_interfaces()
        exp_network_ips = []
        for interface in interfaces:
            network = interface.toDict()['network']
            if 'l3_meas_net' not in network:
                exp_network_ips.append(interface.get_ip_addr())

        return exp_network_ips
      

        
class OwlMf(Owl):
    """
    To be used when interacting with OWL on an MF slice with a measurement node.
    Initializes with the default MF paths for remote conf and out directories.
    """
    
    def __init__(self, local_owl_dir):
        
        # Remote outfile is already specified by MF
        super(OwlMf, self).__init__(local_owl_dir = local_owl_dir,
                                    remote_out_dir = '/home/mfuser/services/owl/output', 
                                    remote_conf_dir = None)

   
        
class OwlDocker(Owl):
    """
    To be used when running OWL (on a non-MF slice) through directly interacting with
    Docker OWL image/containers.
    """

    def __init__(self, local_owl_dir, remote_out_dir, 
                 image_name="fabrictestbed/owl:0.1.3", 
                 remote_conf_dir=None):
        """
        Additional arg of imate_name for Docker.
        
        :param image_name: Docker image to be pulled from docker hub
        :type image_name: str
        """
        super(OwlDocker, self).__init__(local_owl_dir = local_owl_dir,
                                        remote_out_dir = remote_out_dir,
                                        remote_conf_dir = remote_conf_dir)
        
        # Docker image name
        self.image_name = image_name
        

    def pull_owl_docker_image(self, node):
        """
        Pull Docker OWL image to remote node.
        
        :param node: remote node
        :type node: fablib.Node
        """        
        print(f"\n Pulling OWL docker image on {node.get_name()}")
        node.execute(f"sudo docker pull {self.image_name}")


    def start_owl_sender(self, src_node, dst_ip, 
                         name='fabric-owl', 
                         frequency=0.5, 
                         seq_n=1234, 
                         duration=180, 
                         python_time=False):
        """
        Start Docker container to run OWL sender.
        
        :param src_node: OWL source node
        :type src_node: fablib.Node
        :param dst_ip: destination IPv4 address
        :type dst_ip: str
        :param name: container name
        :type name: str
        :param frequency: interval (sec) at which probe packets should be sent
        :type frequency: float
        :param duration: duration (sec) OWL should run
        :type duration: int
        :param python_time: True = timestamp obtained through Python time.time_ns(); 
                            False = timestamp obtained through OWL ptp timestamp script
        :type python_time: bool
        """


        # Container will be removed
        src_cmd = f'sudo docker run -dp 5005:5005 \
                    --rm \
                    --network="host"  \
                    --pid="host" \
                    --privileged \
                    --name {name} \
                    {self.image_name}  sock_ops/udp_sender.py  \
                    --ptp-so-file "/MeasurementFramework/user_services/owl/owl/sock_ops/time_ops/ptp_time.so" \
                    --dest-ip {dst_ip} --dest-port 5005 --frequency {frequency} \
                    --seq-n {seq_n} --duration {duration}'
        
        if python_time:
            # Just use Python time.time_ns() for timestamping
            src_cmd += '--sys-clock'

        src_node.execute(src_cmd)

        
    def start_owl_receiver(self, dst_node, receiving_ip, 
                           name='fabric-owl', 
                           pcap_time_limit=360, 
                           duration=180):
        """
        Start Docker container to run OWL receiver.
        
        :param dst_node: OWL destination node
        :type dst_node: fablib.Node
        :param receiving_ip: IPv4 address of dst node where OWL packets are expected.
        :type receiving_ip: str
        :param name: container name
        :type name: str
        :param pcap_time_limit: time interval (sec) at which tcpdump starts a new pcap file.
        :type pcap_time_limit: int
        :param duration: duration (sec) OWL should run
        :type duration: int
        """
        
        # Container will be removed
        dst_cmd = f'sudo docker run -dp 5005:5005 \
        --rm \
        --mount type=bind,source={self.remote_out_dir},target=/owl_output \
        --network="host"  \
        --pid="host" \
        --privileged \
        --name {name} \
        {self.image_name}  sock_ops/udp_capturer.py \
        --ip {receiving_ip} \
        --port 5005 \
        --pcap-sec {pcap_time_limit} \
        --outdir /owl_output \
        --duration {duration}'

        dst_node.execute(dst_cmd)
        
        
    def stop_owl_docker(self, node, name='fabric-owl'):
        """
        Stop container.
        
        :param node: remote node
        :type node: fablib.Node
        :param name: container name
        :type name: str
        """
        
        print(f"\nStopping OWL container on {node.get_name()}")
        node.execute(f"sudo docker stop {name}")  

        
    def get_owl_log(self, node, name='fabric-owl'):
        """
        Print the contents of container log while the container is running.
        
        :param node: remote node
        :type node: fablib.Node
        :param name: container name
        :type name: str
        """      
        print(f"\nReading fabric-owl log on {node.get_name()}")
        node.execute(f"sudo docker logs {name}")         

        
    def remove_owl_docker_image(self, node, name='fabric-owl'):
        """
        Remove container with the name given and OWL Docker image saved on the node.
        
        :param node: remote node
        :type node: fablib.Node
        :param name: container name
        :type name: str
        """
        cmd1 = f'sudo docker remove {name} --force'
        cmd2 = f'sudo docker rmi {self.image_name} --force'

        print(f"Remove {name} (if present) on {node.get_name()}")
        node.execute(cmd1)

        print(f"Remove owl image on {node.get_name()}")
        node.execute(cmd2)       

        
    @staticmethod
    def check_node_environment(node):
        """
        Checks whether remote node has PTP and Docker required for running OWL.
        
        :param node: remote node
        :type node: fablib.Node
        """
        
        print(f"\n***** On Node {node.get_name()}...")
        print("\n***** Is PTP is enabled?")
        node.execute("ps -ef | grep phc2sys")
        print("\n*****Is Docker installed?")
        node.execute("docker --help | head")


    
        
