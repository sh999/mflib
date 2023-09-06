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

from fabrictestbed_extensions.fablib.fablib import fablib
import json
from mflib.mflib import MFLib
import time


class ImportTool:
    def __init__(self, node, service, git_repo_path='/home/ubuntu/data-import-containers'):
        """
        Constructor. Builds a base class for the import service (for both ELK and Prometheus)
        - Elk
            - Export
            - Import
        """
        self.repo_path = git_repo_path
        self.node = node
        self.service = service

    def install_docker(self):
        commands = [
            'sudo apt-get update',
            'sudo apt-get install docker -y',
            'sudo apt-get install docker-compose -y',
            'sudo docker -v',
            'sudo docker-compose -v'
        ]
        try:
            for command in commands:
                self.node.execute(command)
        except Exception as e:
            print(f"Fail: {e}")

    def setup_nat64(self, node_name):
        commands = [
            f"sudo sed -i '1s/^/0.0.0.0 {node_name}\\n/' /etc/hosts",
            "sudo sed -i '/nameserver/d' /etc/resolv.conf",
            "sudo sh -c 'echo nameserver 2a00:1098:2c::1 >> /etc/resolv.conf'",
            "sudo sh -c 'echo nameserver 2a01:4f8:c2c:123f::1 >> /etc/resolv.conf'",
            "sudo sh -c 'echo nameserver 2a00:1098:2b::1 >> /etc/resolv.conf'"
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")

    def clone_repository(self):
        try:

            self.node.execute(
                f'sudo git clone https://github.com/jackhancockuky/data-import-containers.git {self.repo_path}')
        except Exception as e:
            print(f"Fail: {e}")

    def start_docker(self):
        try:
            self.node.execute(f'sudo docker-compose -f {self.repo_path}/{self.service}/docker-compose.yml up -d')
        except Exception as e:
            print(f"Fail: {e}")

    def stop_docker(self):
        try:
            self.node.execute(f'sudo docker-compose -f {self.repo_path}/{self.service}/docker-compose.yml down')
        except Exception as e:
            print(f"Fail: {e}")


class ElkExporter(MFLib):
    def __init__(self, slice_name="", local_storage_directory="/tmp/mflib", node_name="meas-node"):
        super().__init__(slice_name, local_storage_directory)
        try:
            self.node = self.slice.get_node(name=node_name)
        except Exception as e:
            print("Yeah")
            print(f"Fail: {e}")
        

    def create_repository(self, repository_name):
        self._ensure_dir_permissions()
        """
        registers a snapshot repo using elk rest api
        Args:
            repository_name(str): name of the repo to be created 
        """
        snapshot_directory = "/usr/share/elasticsearch/backup"
        cmd = f'curl -X PUT "http://localhost:9200/_snapshot/{repository_name}?pretty" -H "Content-Type: application/json" -d \'{{ "type": "fs", "settings": {{ "location": "{snapshot_directory}" }} }}\''
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def create_snapshot(self, repository_name, snapshot_name):
        """
        creates a snapshot repo using elk rest api
        Args:
            repository_name(str): name of the repo to be created 
            snapshot_name(str): name of the snapshot to be created
        """

        cmd = f'curl -X PUT "http://localhost:9200/_snapshot/{repository_name}/{snapshot_name}?wait_for_completion=true&pretty" -H "Content-Type: application/json" -d \'"ignore_unavailable": true, "include_global_state": false\''
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def export_snapshot_tar(self, snapshot_name):
        self._ensure_dir_permissions()
        commands = [
            'sudo mkdir -p /home/mfuser/services/elk/files/snapshots',
            f'sudo tar -cvf /home/mfuser/services/elk/files/snapshots/{snapshot_name}.tar -C /var/lib/docker/volumes/elk_snapshotbackup .',
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")
        self.view_snapshot_directory()

    def _ensure_dir_permissions(self):
        commands = [
            'sudo chown -R 1000:1000 /var/lib/docker/volumes/elk_snapshotbackup',
            'sudo chown -R 1000:1000 /var/lib/docker/volumes/elk_snapshotbackup/_data',
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")

    ##### Query ELK data #####

    # View available indices
    def view_indices(self):
        """
        show existing elk indices using elk rest api
        
        """
        cmd = f'curl "http://localhost:9200/_cat/indices?v"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    # View a repository
    def view_repository(self, repository_name):
        """
        show existing elk repository using elk rest api
        
        """
        cmd = f'curl -X GET "http://localhost:9200/_cat/snapshots/{repository_name}?pretty"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def view_snapshot(self, repository_name, snapshot_name):
        """
        show elk snapshot inside repository using elk rest api
        """
        cmd = f'curl -X GET "http://localhost:9200/_snapshot/{repository_name}/{snapshot_name}?pretty"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def view_snapshot_directory(self):
        commands = [
            'echo snapshots in directory on measurement node:',
            'ls /home/mfuser/services/elk/files/snapshots/'
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")


class PrometheusExporter(MFLib):
    def __init__(self, slice_name, local_storage_directory="/tmp/mflib", node_name="meas-node"):
        super().__init__(slice_name, local_storage_directory)
        try:
            self.node = self.slice.get_node(name=node_name)
        except Exception as e:
            print(f"Fail: {e}")

    def create_snapshot(self, user, password):
        try:
            stdout = self.node.execute(
                f'sudo curl -k -u {user}:{password} -XPOST https://localhost:9090/api/v1/admin/tsdb/snapshot?skip_head=false')
            return json.loads(stdout[0])["data"]["name"]
        except Exception as e:
            print(f"Fail: {e}")

    def export_snapshot_tar(self, snapshot_name):
        commands = [
            'sudo mkdir -p /home/mfuser/services/prometheus/files/snapshots',
            f'sudo tar -cvf /home/mfuser/services/prometheus/files/snapshots/{snapshot_name}.tar -C /opt/data/fabric_prometheus/prometheus/snapshots .',
        ]
        for command in commands:
            try:
                self.node.execute(command=command, quiet=True)
            except Exception as e:
                return f"Fail: {e}"
        return f"Successfully exported {snapshot_name} to /home/mfuser/services/prometheus/files/snapshots/"

    def view_snapshot_directory(self):
        commands = [
            'echo snapshots in directory on measurement node:',
            'ls /home/mfuser/services/prometheus/files/snapshots/'
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")


class ElkImporter(ImportTool):
    def __init__(self, slice_name, node_name, git_repo_path='/home/ubuntu/data-import-containers'):
        self.slice_name = slice_name
        try:
            self.slice = fablib.get_slice(name=self.slice_name)
        except Exception as e:
            print(f"Fail: {e}")
        try:
            self.node = self.slice.get_node(name=node_name)
        except Exception as e:
            print(f"Fail: {e}")
        super().__init__(self.node, "elk", git_repo_path)

    def import_snapshot(self, snapshot_file_name):
        """
        Untars snapshot file, creates repository directory and places snapshot data inside.
        Args:
        snapshot_file_name(str): ELK snapshot file name
        snapshot_file_path(optional, str): ELK Snapshot file path on node (Defaults to snapshot 
        repository_directory(optional, str): ELK Repository directory path on node (Defaults to git repo settings)
        """
        try:
            self.node.execute(f"echo uploading {snapshot_file_name} to measurement node..")
            self.node.upload_file(f"./snapshots/{snapshot_file_name}", f'/tmp/{snapshot_file_name}')
        except Exception as e:
            print(f"Fail: {e}")

        commands = [
            "echo 'Creating imported_data directory..'",
            f"sudo mkdir {self.repo_path}/{self.service}//imported_data",
            "echo 'Moving snapshot file..'",
            f"sudo mv /tmp/{snapshot_file_name} {self.repo_path}/{self.service}/snapshots/",
            "echo 'Untarring snapshot data into shared docker volume..'",
            f"sudo tar -xvf {self.repo_path}/{self.service}/snapshots/{snapshot_file_name} -C {self.repo_path}/{self.service}/imported_data"
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")

    def register_repository(self, repository_name):
        cmd = f'curl -X PUT -H "Content-Type: application/json" -d \'{{"type": "fs", "settings": {{"location": "/usr/share/elasticsearch/imported_data/_data", "compress": true }} }}\' http://localhost:9200/_snapshot/{repository_name}'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def restore_snapshot(self, repository_name, snapshot_name):
        """
        Deletes indices currently on ELK and replaces with desired snapshot data
        Args:
            repository_name(str): ELK Repository name
            snapshot_name(str): ELK Snapshot name
        """
        cmds = ['curl -X DELETE "http://localhost:9200/_all"',
                f'curl -X POST "http://localhost:9200/_snapshot/{repository_name}/{snapshot_name}/_restore?pretty" -H "Content-Type: application/json" -d \'{{"indices": "*", "index_settings": {{"index.number_of_replicas": 1 }} }}\'']
        for cmd in cmds:
            try:
                self.node.execute(cmd)
                time.sleep(5)
            except Exception as e:
                print(f"Fail: {e}")

    def remove_data(self):
        commands = [
            'sudo docker volume rm elk_es-data',
            f'sudo rm -rf {self.repo_path}/imported_data/*'
        ]
        try:
            for command in commands:
                self.node.execute(command)
        except Exception as e:
            print(f"Fail: {e}")

    ##### Query ELK data #####

    # View available indices
    def view_indices(self):
        """
        show existing elk indices using elk rest api
        
        """
        cmd = f'curl "http://localhost:9200/_cat/indices?v"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    # View a repository
    def view_repository(self, repository_name):
        """
        show existing elk repository using elk rest api
        
        """
        cmd = f'curl -X GET "http://localhost:9200/_cat/snapshots/{repository_name}?pretty"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")

    def view_snapshot(self, repository_name, snapshot_name):
        """
        show elk snapshot inside repository using elk rest api
        """
        cmd = f'curl -X GET "http://localhost:9200/_snapshot/{repository_name}/{snapshot_name}?pretty"'
        try:
            self.node.execute(cmd)
        except Exception as e:
            print(f"Fail: {e}")


class PrometheusImporter(ImportTool):
    def __init__(self, slice_name, node_name, git_repo_path='/home/ubuntu/data-import-containers'):
        self.slice_name = slice_name
        try:
            self.slice = fablib.get_slice(name=self.slice_name)
        except Exception as e:
            print(f"Fail: {e}")
        try:
            self.node = self.slice.get_node(name=node_name)
        except Exception as e:
            print(f"Fail: {e}")
        super().__init__(self.node, "prometheus", git_repo_path)

    def import_snapshot(self, snapshot_file_name):
        """
        Uploads snapshot file into correct place on meas_node then runs import_snapshot.sh to import snapshot.
        Args:
        snapshot_file_name(str): Prometheus snapshot file name
        """
        commands = [
            "echo 'Importing snapshot into Prometheus..'",
            f"sudo {self.repo_path}/{self.service}/import_snapshot.sh /tmp/{snapshot_file_name} {self.repo_path}/{self.service}/snapshots"
        ]
        for command in commands:
            try:
                self.node.execute(command)
            except Exception as e:
                print(f"Fail: {e}")