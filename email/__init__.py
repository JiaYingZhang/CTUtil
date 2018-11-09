from CTUtil.email.util import CingTaEmail
from django.core.mail import send_mail
from collections import namedtuple
from typing import List, Union
from traceback import print_exc

_state = namedtuple('STATE', ['SUCCESS', 'FAIL'])
state = _state(1, -1)


def send_cingta_email(
        title: str,
        to_email: List[str],
        model: Union[None, str]=None,
        msg: Union[None, str]=None,
        from_email_name: str='cingta',
        **kwargs) -> int:
    mail: Email = CingTaEmail(title, to_email, model, msg, from_email_name, **kwargs)
    try:
        send_mail(**mail.email_msg)
        return state.SUCCESS
    except BaseException as e:
        print_exc()
        return state.FAIL
