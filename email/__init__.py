from CTUtil.email.util import CingTaEmail
from django.core.mail import send_mail
from typing import List, Union, Type
from traceback import print_exc
from CTUtil.types import EmailTypes, FuncCallBack


def send_cingta_email(
        title: str,
        to_email: List[str],
        model: Type[EmailTypes]=EmailTypes.DEMAND,
        msg: Union[None, str]=None,
        from_email_name: str='cingta',
        **kwargs) -> Type[FuncCallBack]:
    mail: Email = CingTaEmail(title, to_email, model, msg, from_email_name, **kwargs)
    try:
        send_mail(**mail.email_msg)
        return FuncCallBack.SUCCESS
    except BaseException as e:
        print_exc()
        return FuncCallBack.FAIL
