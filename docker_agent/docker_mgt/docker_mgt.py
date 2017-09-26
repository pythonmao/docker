import contextlib
import os
from os import path
import shutil
import uuid
import portpicker
import time
import threading
from docker import client
from docker import errors
from exception import InvalidParamter
from log import logger

__author__ = 'maohaijun'

# record container time, format {container_id: start_time,}
status_instance_threads = dict()
# record image load status, format {container_id: start_time,}
status_image_threads = dict()


@contextlib.contextmanager
def docker_client():
    try:
        yield client.Client(
            base_url='unix:///var/run/docker.sock',
            version='1.22',
            timeout=300,
        )
    except errors.APIError as e:
        raise


class DockerDriver(object):
    '''Implementation of container drivers for Docker.'''

    def load_image(self, image_path):
        if os.path.isfile(image_path):
            logger.debug('Start loading image:%s thread' % image_path)
            image_id = str(uuid.uuid1())
            status_image_threads[image_id] = 'loading'
            threading.Thread(target=self._load_image_thread, args=(image_id, image_path)).start()
            return image_id
        else:
            msg = 'The parameter image_path: %s is not exist' % image_path
            logger.error(msg)
            raise InvalidParamter(reason=msg)

    def _load_image_thread(self, image_id, image_path):
        with docker_client() as docker:
            logger.debug('Loading image %s' % image_path)
            try:
                with open(image_path, 'r') as fd:
                    docker.load_image(fd.read())
                status_image_threads[image_id] = 'deploy'
            except Exception as e:
                logger.error("Load image failed, reason: %s" % e)
                status_image_threads[image_id] = 'error'
            # wait head node get status
            time.sleep(60)
            status_image_threads.pop(image_id)

    def get_image_status(self, image_id):
        if image_id not in status_image_threads:
            logger.error("The image id is invalid")
            return 'unknown'
        return status_image_threads[image_id]

    def create_container(self, **kwargs):
        self._check_creation_args(**kwargs)

        with docker_client() as docker:
            docker_kwargs = {
                # 'name': '',
                'ports': kwargs.get('ports', None),
                'environment': kwargs.get('env', None),
                # 'working_dir': kwargs['workspace'],
                # 'labels': labels,
                'tty': True,
                'stdin_open': True,
            }

            # generate host config
            host_config = self._generate_host_config(**kwargs)
            docker_kwargs['host_config'] = docker.create_host_config(**host_config)
            # generate new command with log
            command = self._generate_new_command(kwargs.get('log_path'),
                                                 kwargs['workspace'], kwargs.get('command'))
            docker_kwargs['command'] = command
            # create
            response = docker.create_container(kwargs['image'], **docker_kwargs)
            container_id = response['Id']
            # start
            docker.start(container_id)

            # start monitor thread
            threading.Thread(target=self._status_monitor, args=(container_id,)).start()
            status_instance_threads[container_id] = time.time()
            return container_id

    def _check_creation_args(self, **kwargs):
        if not kwargs.get('image', None):
            msg = "The parameter image: %s is not exist" % kwargs['image']
            logger.error(msg)
            raise InvalidParamter(reason=msg)

        if not os.path.exists(kwargs['workspace']):
            msg = "The parameter workspace: %s is not exist" % kwargs['workspace']
            logger.error(msg)
            raise InvalidParamter(reason=msg)

    def _generate_host_config(self, **kwargs):
        host_config = {}
        memory = kwargs['resource'].get('memory', 0)
        if memory:
            host_config['mem_limit'] = memory

        cpu = kwargs['resource'].get('cpus', 0)
        if cpu:
            host_config['cpu_quota'] = int(100000 * int(cpu))
            host_config['cpu_period'] = 100000

        gpu_list = kwargs['resource'].get('gpus', [])
        if gpu_list:
            host_config['devices'] = map(lambda v: {'PathOnHost': '/dev/nvidia' + str(v),
                                                    'PathInContainer': '/dev/nvidia' + str(v),
                                                    "CgroupPermissions": "mrw"}, gpu_list)
        port_list = kwargs.get('ports', None)
        if port_list:
            temp_list = dict()
            for port in port_list:
                temp_list[str(port) + '/tcp'] = [{'HostPort': str(port), 'HostIp': '0.0.0.0'}]
            host_config['port_bindings'] = temp_list

        workspace = kwargs.get('workspace', None)
        if workspace:
            bind_dir = workspace.strip() + ':' + workspace.strip()
            host_config['binds'] = [bind_dir]

        host_config['network_mode'] = 'host'
        host_config['log_config'] = {"type": "json-file"}
        # host_config['privileged'] = True
        return host_config

    def _generate_new_command(self, log_path, workspace, command):
        if not command:
            return
        if not log_path:
            log_path = path.join(workspace, 'undefine.log')

        current_path = path.abspath(path.dirname(__file__))
        source_script = path.join(current_path, 'template.sh')
        shutil.copy(source_script, workspace)
        dest_script = path.join(workspace, 'template.sh')
        command = '%s %s "%s"' % (dest_script, log_path, command)
        return command

    def delete(self, container_id):
        with docker_client() as docker:
            try:
                docker.remove_container(container_id, force=True)
            except errors.APIError as api_error:
                if '404' in str(api_error):
                    return
                raise

    def get_instance_status(self, container_id):
        # update monitor status
        if container_id in status_instance_threads:
            status_instance_threads[container_id] = time.time()

        with docker_client() as docker:
            try:
                response = docker.inspect_container(container_id)
            except errors.APIError as api_error:
                if '404' in str(api_error):
                    return 'error'
                raise

        return self._parser_status(response.get('State'))

    def _status_monitor(self, container_id):
        while True:
            time.sleep(5)
            current_time = time.time()
            if current_time - status_instance_threads[container_id] > 60:
                self.delete(container_id)
                break
        status_instance_threads.pop(container_id)

    def _parser_status(self, status):
        if status:
            if status.get('Error') is True:
                return 'error'
            elif status.get('Paused'):
                return 'pause'
            elif status.get('Running'):
                return 'running'
            elif status.get('Creating'):
                return 'creating'
            elif status.get('Stopped'):
                return 'stopped'
            elif status.get('Dead'):
                return 'dead'
            elif status.get('Restarting'):
                return 'restarting'
            elif status.get('Status'):
                return status['Status']

        return 'unknown'

    def stop(self, container_id):
        with docker_client() as docker:
            docker.stop(container_id)

    def get_free_port(self, num):
        if num <= 0:
            return []

        port_list = list()
        while True:
            port = portpicker.pick_unused_port()
            if port not in port_list:
                port_list.append(port)
            if len(port_list) == num:
                break
        return port_list
