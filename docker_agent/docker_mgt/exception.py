from exceptions import Exception
from log import logger

__author__ = 'maohaijun'


class AgentException(Exception):
    message = "An unkonwn message exception occurred."

    def __init__(self, message=None, **kwargs):
        if not message:
            try:
                message = self.message % kwargs
            except Exception as e:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                for name, value in kwargs.items():
                    logger.error("%s: %s" % (name, value))
                message = self.message

        super(AgentException, self).__init__(message)


class InvalidParamter(AgentException):
    message = "The parameter is invalid, reason:%(reason)s."
