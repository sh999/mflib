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


import csv
from decimal import Decimal
from pathlib import Path
from glob import glob
#from configparser import ConfigParser
from scapy.all import *


import numpy as np
import pandas as pd
import plotly.graph_objects as go

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager


def list_pcap_files(root_dir):
    """
    Search recursively for pcap files under root_dir
    
    :param root_dir: Directory that will be treated as root for this search
    :type root_dir: str
    :return files_list: absolute paths for all the *.pcap files under the root_dir
    :rtype: [posix.Path]
    """
    
    files_list = []
    
    for path in Path(root_dir).rglob('*.pcap'):
        files_list.append(path.resolve())
    
    return files_list


def convert_pcap_to_csv(pcap_files, outfile="out.csv", append_csv=False, verbose=False):
    """
    Extract data from the list of pcap files and write to one csv file.
    
    :param pcap_files: list of pcap file paths
    :type pcap_files: [posix.Path]
    :param outfile: name of csv file
    :type outfile: str
    :param append_csv: whether to append data to an existing csv file of that name
    :type append_csv: bool
    :param verbose: if True, prints each line as it is appended to csv
    :type verbose: bool

    """

    # TODO: Check if the csv file exists
    
    if append_csv is False:
        if os.path.isfile(outfile):
            print(f"CSV file {outfile} already exists. Either delete the file or pass \
            append_csv=True")
            
            return 
    

    # Remove zero-bye pcap files
    pcapfiles_with_data = [str(f) for f in pcap_files if os.stat(f).st_size > 0]
    print("non-zero pcap files to be processed: ", pcapfiles_with_data)

    # Extract data
    for pcapfile in pcapfiles_with_data:
        print("file name:",  pcapfile)
        pkts = rdpcap(pcapfile)

        for pkt in pkts:
            # Fields are <src-ip, send-t,  
            #             dst-ip, dst-t,  seq-n, latency_nano>
            # latency_nano is in nano-seconds

            fields=[]

            # Field: src-ip
            try:
                fields.append(str(pkt[IP].src))
            except(IndexError) as e:
                print("\nEncountered an issue reading source IP")
                print(e)

            # Field: send-t
            try:
                send_t, seq_n = pkt[Raw].load.decode().split(",")
                send_t = Decimal(send_t)  # To prevent floating point issues
                fields.append(str(send_t))
            except (ValueError, IndexError) as e: 
                print("\nEncountered an issue reading payload data")
                print(e)
               
            # Field: dst-ip
            try:
                fields.append(str(pkt[IP].dst))
            except(IndexError) as e:
                print("\nEncountered an issue reading destination IP")
                print(e)
                
            # Field: dst-t
            try:
                fields.append(str(pkt.time))  # pkt.time is type Decimal
            except(IndexError) as e:
                print("\nEncountered an issue reading received time")
                print(e)
                
            # Field: seq-n
            try:
                fields.append(seq_n)
            except(ValueError) as e:
                print("\nEncountered an issue reading payload data")
                print(e)            

            # Field: latency
            try:
                latency_nano = (pkt.time-send_t)*1000000000
                fields.append(str(int(latency_nano)))
            except(ValueError) as e:
                print(e)

            if verbose:
                print(fields)


            with open(outfile, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(fields)   


class OwlDataAnalyzer():
    
    def __init__(self, owl_csv):
        """
        Helper class for analyzing and visualizing OWL output data
        
        :param owl_csv: csv file containing data extracted from pcap files.
        :type owl_csv: str
        """
        
        owl_df = pd.read_csv(owl_csv, 
                             header=None, 
                             names=["src_ip", "sent_t", "dst_ip", "dst_t", "seq_n", "latency"])
        
        # Data cleaning
        owl_df['src_ip'] = owl_df['src_ip'].astype('str')
        owl_df['sent_t'] = pd.to_numeric(owl_df['sent_t'], errors='coerce')
        owl_df['sent_t_datetime'] = pd.to_datetime(owl_df['sent_t'], unit='s', errors='coerce')
        owl_df['dst_t'] = pd.to_numeric(owl_df['dst_t'], errors='coerce')
        owl_df['dst_t_datetime'] = pd.to_datetime(owl_df['dst_t'], unit='s', errors='coerce')
        owl_df['seq_n'] = pd.to_numeric(owl_df['seq_n'], errors='coerce')
        owl_df['latency'] = pd.to_numeric(owl_df['latency'], errors='coerce')
        owl_df = owl_df.dropna(how='any')
        owl_df['latency'] = owl_df['latency'].astype(int)
        
        self.owl_df = owl_df.dropna(how='any')
 

    def get_dataframe(self):
        """
        Get the cleansed data
        
        :rtype: pandas.DataFrame
        """
        return (self.owl_df)
    
    
    def summarize_data(self, src_node, dst_node, src_ip=None, dst_ip=None):
        """
        Print summary of latency data collected between source and destination nodes
        
        :param src[dst]_node: source/destination nodes
        :type src[dst]_node:fablib.Node
        :param src[dst]_ip: needed only if there are multiple experimenter IP interfaces
        :type src[dst]_ip: str
        """

        # If IP addresses not given, assume there is only 1

        if not src_ip:
            src_ip = self.list_experiment_ip_addrs(src_node)[0]
        if not dst_ip:
            dst_ip = self.list_experiment_ip_addrs(dst_node)[0]

        f_data = self.filter_data(src_ip, dst_ip)
        
        print(f"\n*****{src_ip} ({src_node.get_site()}) --> {dst_ip} ({dst_node.get_site()})")
        print(f"Number of samples {len(f_data.index)}")
        print(f"Median Latency (ns): {f_data['latency'].median()}")
        print(f"Median Latency (micros): {(f_data['latency'].median())/1000}")
        print(f"Median Latency (ms): {(f_data['latency'].median())/1000000}")
        print(f"Median Latency (s): {(f_data['latency'].median())/1000000000}")
        print(f"max latency (ns): {f_data['latency'].max()}")
        print(f"min latency (ns): {f_data['latency'].min()}")
        print("\n***Compare the result to ping")
        stdout, stderr = src_node.execute(f"ping -c 2 {dst_ip}")


    def filter_data(self, src_ip, dst_ip):
        """
        Filter data by source and destination IPs
        
        :param src[dst]_ip: Source and destination IPv4 addresses
        :type src[dst]_ip: str
        """
            
        return self.owl_df.loc[(self.owl_df['src_ip']==src_ip) &
                               (self.owl_df['dst_ip']==dst_ip)]          

    
    
    def graph_latency_data(self, src_node, dst_node, src_ip=None, dst_ip=None):
        """
        Graph latency data collected between source and destination nodes
        
        :param src[dst]_node: source/destination nodes
        :type src[dst]_node:fablib.Node
        :param src[dst]_ip: needed only if there are multiple experimenter IP interfaces
        :type src[dst]_ip: str
        """       

        if not src_ip:
            src_ip = self.list_experiment_ip_addrs(src_node)[0]
        if not dst_ip:
            dst_ip = self.list_experiment_ip_addrs(dst_node)[0]
            
        filtered = self.filter_data(src_ip, dst_ip)
        # import plotly.io as pio
        # pio.renderers.default = 'iframe'


        fig = go.Figure([go.Scatter(x=filtered['sent_t_datetime'],
                                    y=filtered['latency'])])
        fig.update_layout(
            title = f'{src_ip} ({src_node.get_site()}) -> {dst_ip} ({dst_node.get_site()})',
            xaxis_title = "Sent time",
            yaxis_title = "latency in nano-sec",
            yaxis = dict(
                    tickformat='d'))
        
        fig.show()



    def find_node_locations(self, nodes):
        """
        Print site information for nodes
        
        :param nodes: nodes whose data to be printed
        :type nodes: fablib.Node
        :return: node name, site name, location and experimenter IPv4 (only the first if multiple)
        :rtype: pandas.DataFrame
        """
        
        fablib = fablib_manager()
        r = fablib.get_resources()
        
        df = pd.DataFrame(columns = ['node_name', 'site_name', 'lon', 'lat', 'exp_ip'])
        for node in nodes:
            node_name = node.get_name()
            
            if node_name == "meas-node":
                pass
            else: 
                site_name = node.get_site()
                lat, lon = r.get_location_lat_long(site_name)
                node_ip = self.list_experiment_ip_addrs(node)[0]

                new_row = pd.DataFrame([{
                                'node_name': node_name,
                                'site_name': site_name,
                                'lon': lon,
                                'lat': lat,
                                'exp_ip': node_ip}])
                df = pd.concat([df, new_row]) 
                
        return df
   

    @staticmethod
    def print_map(df):
        """
        Print a map with nodes/sites data for fun.
        
        :param df: Pandas.DataFrame with columns 'node_name', 'site_name', 'lon', 'lat', 'exp_ip'
        :type df: Pandas.DataFrame
        """
        
        

        fig = go.Figure(data=go.Scattergeo(
                lon = df['lon'],
                lat = df['lat'],
                text = df['site_name'] + '; ' + df['exp_ip'],
                marker=dict(size=8, color="blue")
                ))

        fig.update_layout(
                title = 'Slice nodes',
                geo_scope='world',
            )
        fig.show()
    
    
    @staticmethod
    def list_experiment_ip_addrs(node):
        """
        Get experimenter IPv4 addresses for each node. 
        
        :param node: Node on which IPv4 address is queried.
        :type node: fablib.Node
        :return: a list of of IPv4 addresses assigned to node interfaces
        :rtype: [str]
        """
        
        # The following line excludes management net interface
        interfaces = node.get_interfaces()
        exp_network_ips = []
        for interface in interfaces:
            network = interface.toDict()['network']
            if 'l3_meas_net' not in network:
                exp_network_ips.append(interface.get_ip_addr())

        return exp_network_ips 
