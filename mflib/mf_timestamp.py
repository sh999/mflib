# MIT License
#
# Copyright (c) 2022 FABRIC Testbed
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

import json
from mflib import mflib
import os
import sys
import time
import requests
from fabrictestbed_extensions.fablib.fablib import fablib
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class mf_timestamp():
    #sanity_version = "2.01"
    
    def __init__(self, slice_name, container_name):
        """
        Constructor. Builds Manager for mf_timestamp object.
        """
        super().__init__()
        self.slice_name=slice_name
        self.container_name=container_name
        try:
            self.slice = fablib.get_slice(name=self.slice_name)
        except Exception as e:
            print(f"Fail: {e}")
        
            
    def record_packet_timestamp(self, node, name, interface, ipversion, protocol, duration, host=None, port=None, verbose=False):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        base_cmd = f"sudo docker exec -i {self.container_name} python3 /root/services/timestamp/service_files/timestamptool.py record packet"
        name_cmd = f"-n {name}"
        interface_cmd = f"-i {interface}"
        ipversion_cmd = f"-ipv {ipversion}"
        protocol_cmd = f"-proto {protocol}"
        duration_cmd= f"-durn {duration}"
        #storage_cmd= f"-stg {storage}"
        cmd= f"{base_cmd} {name_cmd} {interface_cmd} {ipversion_cmd} {protocol_cmd} {duration_cmd} "
        if host:
            host_cmd = f"-host {host}"
            cmd= f"{cmd} {host_cmd}"
        if port:
            port_cmd = f"-port {port}"
            cmd = f"{cmd} {port_cmd}"
        if verbose is True:
            verbose_cmd = f"-v" 
            cmd = f"{cmd} {verbose_cmd}"
        print (f"The docker command is: {cmd}")
        stdout, stderr= node.execute(cmd)

            
    def record_event_timestamp(self, node, name, event, description=None, verbose=False):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        base_cmd = f"sudo docker exec -i {self.container_name} python3 /root/services/timestamp/service_files/timestamptool.py record event"
        name_cmd = f"-n {name}"
        event_cmd = f"-event {event}"
        cmd= f"{base_cmd} {name_cmd} {event_cmd} "
        if description:
            desc_cmd = f"-desc {description}"
            cmd= f"{cmd} {desc_cmd}"
        if verbose is True:
            verbose_cmd = f"-v" 
            cmd = f"{cmd} {verbose_cmd}"
        print (f"The docker command is: {cmd}")
        stdout, stderr= node.execute(cmd)
        
            
    def get_packet_timestamp(self, node, name, verbose=False):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        base_cmd = f"sudo docker exec -i {self.container_name} python3 /root/services/timestamp/service_files/timestamptool.py get packet"
        name_cmd = f"-n {name}"
        #storage_cmd= f"-stg {storage}"
        cmd= f"{base_cmd} {name_cmd} "
        if verbose is True:
            verbose_cmd = f"-v" 
            cmd = f"{cmd} {verbose_cmd}"
        #print (f"The docker command is {cmd}")
        stdout, stderr= node.execute(cmd)
        json_obj=json.loads(str(stdout))
        return (json_obj)
        
        
    def get_event_timestamp(self, node, name, verbose=False):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        base_cmd = f"sudo docker exec -i {self.container_name} python3 /root/services/timestamp/service_files/timestamptool.py get event"
        name_cmd = f"-n {name}"
        #storage_cmd= f"-stg {storage}"
        cmd= f"{base_cmd} {name_cmd}"
        if verbose is True:
            verbose_cmd = f"-v" 
            cmd = f"{cmd} {verbose_cmd}"
        #print (f"The docker command is {cmd}")
        stdout, stderr= node.execute(cmd)
        json_obj=json.loads(str(stdout))
        return (json_obj)
    
    def plot_packet_timestamp(self, json_obj):
        x_labels = []
        y_labels = []
        count=0
        for item in json_obj:
            sec = item["timestamp"].split(".")[0].split("T")[1]
            if sec not in x_labels:
                if (count!=0):
                    y_labels.append(count)
                x_labels.append(sec)
                count = 0
            count+=1
        y_labels.append(count)
        fig = plt.figure(figsize = (25, 10))
        plt.bar(x_labels,y_labels,width = 0.2)
        plt.xlabel("Timestamp")
        plt.ylabel("No. of Packets Captured")
        plt.title("Packets Captured Over Time")
        

        for i in range(len(y_labels)):
            plt.annotate(str(y_labels[i]), xy=(x_labels[i],y_labels[i]), ha='center', va='bottom')
        plt.show()
        
        
    def plot_event_timestamp(self, json_obj):
        x_labels=[]
        y_labels=[]
        annotation=[]
        for item in json_obj:
            sec = item["timestamp"]
            x_labels.append(sec)
            y_labels.append(1)
            annotation.append(item["name"])
        fig = plt.figure(figsize = (15, 6))
        plt.bar(x_labels,y_labels,width = 0.4)
        plt.xlabel("Timestamp")
        plt.ylabel("No. of Events Captured")
        plt.title("Events Captured")
        
        for i in range(len(y_labels)):
            plt.annotate(str(annotation[i]), xy=(x_labels[i],y_labels[i]), ha='center', va='bottom')
        plt.show()
        
        
    def upload_influx(self, node, data_type, bucket, org, token):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        command = f"sudo docker exec -i timestamp python3 /root/services/timestamp/service_files/influxdb_manager.py upload {data_type} -b {bucket} -o {org} -t {token}"
        print (f"The docker command is: {command}")
        stdout, stderr= node.execute(command)
        
        
    def download_influx(self, node, data_type, bucket, org, token, name):
        try:
            node = self.slice.get_node(name=node)
        except Exception as e:
            print(f"Fail: {e}")
        command = f"sudo docker exec -i timestamp python3 /root/services/timestamp/service_files/influxdb_manager.py download {data_type} -b {bucket} -o {org} -t {token} -n {name}"
        #print (f"The docker command is {command}")
        stdout, stderr= node.execute(command)
        
        
    def deploy_influxdb_dashboard(self, dashboard_file):
        
        # Upload the dashboard file to the directory on meas_node that binds mount on influxdb container
        meas_node_name = "_meas_node"
        try:
            meas_node = self.slice.get_node(name=meas_node_name)
        except Exception as e:
            print(f"Fail: {e}")
        meas_node.upload_file(local_file_path=dashboard_file, remote_file_path="/home/mfuser/influxdb/dashboard.yml")
        
        # Apply the template in influxdb 
        command = f"sudo docker exec -i influxdb influx apply --skip-verify --file /var/lib/influxdb2/dashboard.yml"
        stdout, stderr= meas_node.execute(command)






