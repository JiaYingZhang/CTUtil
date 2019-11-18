from CTUtil.email.util import CingTaEmail, BaseEmail, EmailTemplate
from django.core.mail import send_mail
from typing import List, Union, Type

__all__ = ('CingTaEmail', 'BaseEmail', 'send_mail', 'EmailTemplate'
           'FuncCallBack')


def send_cingta_email(title: str,
                      to_email: List[str],
                      model: Type[EmailTemplate],
                      msg: Union[None, str] = None,
                      from_email_name: str = 'cingta',
                      **kwargs):
    mail: CingTaEmail = CingTaEmail(title, to_email, model, msg,
                                    from_email_name, **kwargs)
    try:
        send_mail(**mail.email_msg)
        return None
    except Exception as e:
        raise e