from django.http import HttpResponse
from CTUtil.types import ResponseStates, EnumJsonEncode

from typing import Dict, Any, Type, Union
import json


def resp_to_json(data: Dict[str, Any], token=None) -> HttpResponse:
    if not isinstance(data, dict):
        raise TypeError('data must be a dict')
    resp = HttpResponse(json.dumps(data, cls=EnumJsonEncode), content_type='application/json')
    resp['Access-Control-Allow-Headers'] = '*'
    resp['Access-Control-Allow-Origin'] = '*'
    resp['Access-Control-Allow-Credentials'] = True
    resp['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    if token:
        resp.setdefault('token', token)
        resp['Access-Control-Expose-Headers'] = 'token'
    return resp


def resp_error_json(error_msg: str, state: Type[ResponseStates] = ResponseStates.NOMAL_ERROR) -> HttpResponse:
    _resp_data: Dict[str, Union[str, int]] = {
        'data': error_msg,
        'state': state,
    }
    return resp_to_json(_resp_data)
