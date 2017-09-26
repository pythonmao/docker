from bottle import Bottle, run
from log import logger
from views import docker_instance_view

__author__ = 'maohaijun'


def setup_routing(app):
    app.route('/dockers', ['POST'], docker_instance_view.create)
    app.route('/dockers/<id:re:[0-9a-zA-Z]+>', ['GET'], docker_instance_view.get_instance_status)
    app.route('/dockers/<id:re:[0-9a-zA-Z]+>', ['DELETE'], docker_instance_view.delete)
    app.route('/dockers/image', ['POST'], docker_instance_view.image_load)
    app.route('/dockers/image/<id:re:[0-9a-zA-Z-]+>', ['GET'], docker_instance_view.get_image_status)
    app.route('/dockers/port', ['GET'], docker_instance_view.get_free_port)


app = Bottle()
setup_routing(app)
if __name__ == '__main__':
    logger.info('Start lico agent server...')
    run(app, host='0.0.0.0', port=9527)
