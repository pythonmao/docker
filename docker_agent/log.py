import logging
from logging.handlers import RotatingFileHandler

__author__ = 'maohaijun'


class Logger(object):
    Rthandler = RotatingFileHandler('/var/log/lico_agent.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    Rthandler.setFormatter(formatter)
    logger = None

    def __init__(self):
        Logger.logger = logging.getLogger()
        Logger.logger.addHandler(Logger.Rthandler)
        Logger.logger.setLevel(logging.DEBUG)

    @staticmethod
    def get_instance():
        if Logger.logger:
            return Logger.logger
        return Logger().logger


logger = Logger.get_instance()
