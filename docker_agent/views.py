from bottle import request
from docker_mgt import docker_mgt

__author__ = 'maohaijun'


class docker_instance(object):
    def create(self):
        msg = container_id = ''
        error_code = 0

        try:
            container_id = docker_mgt.create_container(**request.json)
        except Exception as e:
            error_code = 1
            msg = str(e)

        return {
            'error_code': error_code,
            'msg': msg,
            'data': {
                'id': container_id
            }
        }

    def delete(self, id):
        msg = ''
        error_code = 0

        try:
            docker_mgt.delete(id)
        except Exception as e:
            error_code = 1
            msg = str(e)

        return {
            'error_code': error_code,
            'msg': msg,
            'data': {}
        }

    def image_load(self):
        msg = image_id = ''
        error_code = 0
        image_path = request.json.get('path', '')

        try:
            image_id = docker_mgt.load_image(image_path)
        except Exception as e:
            error_code = 1
            msg = str(e)

        return {
            'error_code': error_code,
            'msg': msg,
            'data': {
                'id': image_id
            }
        }

    def get_image_status(self, id):
        status = docker_mgt.get_image_status(id)

        return {
            'error_code': 0,
            'msg': '',
            'data': {
                'status': status
            }
        }

    def get_instance_status(self, id):
        msg = status = ''
        error_code = 0

        try:
            status = docker_mgt.get_status(id)
        except Exception as e:
            error_code = 1
            msg = str(e)

        return {
            'error_code': error_code,
            'msg': msg,
            'data': {
                'status': status
            }
        }

    def get_free_port(self):
        port_num = request.params.get('num', 1)
        port_list = docker_mgt.get_free_port(int(port_num))

        return {
            'error_code': 0,
            'msg': '',
            'data': {
                'port_list': port_list
            }
        }


docker_instance_view = docker_instance()
