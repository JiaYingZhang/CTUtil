from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from CTUtil.response import resp_error_json
from CTUtil.types import HTTPResponseStates
from traceback import print_exc
from io import StringIO
import logging


__all__ = ['ProcessException']


class ProcessException(MiddlewareMixin):
    def process_response(self, request: HttpRequest, response: HttpResponse):
        if response.status_code == HTTPResponseStates.NOTFOUND:
            resp = resp_error_json('api不存在')
            resp.status_code = HTTPResponseStates.NOTFOUND
            return resp
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        fp = StringIO()
        print_exc(file=fp)
        msg = fp.getvalue()
        fp.close()
        logging.error(format_logging_msg(request.path, msg))
        resp: HttpResponse = resp_error_json('系统错误')
        resp.status_code = HTTPResponseStates.ERROR
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
