from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from CTUtil.util import RespErrorJson
from traceback import print_exc
from io import StringIO
from utils.util import logger, logger_formatter
import logging

__all__ = ['ProcessException']
file = 'error.log'

file_log_handle = logging.FileHandler(file)
file_log_handle.setFormatter(logger_formatter)
logger.addHandler(file_log_handle)


class ProcessException(MiddlewareMixin):
    def process_response(self, request: HttpRequest, response: HttpResponse):
        if response.status_code == 404:
            resp = RespErrorJson('api不存在')
            resp.status_code = 404
            return resp
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        fp = StringIO()
        print_exc(file=fp)
        msg = fp.getvalue()
        fp.close()
        logger.error(format_logging_msg(request.path, msg))
        resp: HttpResponse = RespErrorJson('系统错误')
        resp.status_code = 500
        return resp


def format_logging_msg(path, exception):
    msg: str = f"""
    ##########\n
    path: {path}\n
    exception: \n
    {exception}
    ##########\n
    """
    return msg
