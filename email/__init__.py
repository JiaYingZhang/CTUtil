from CTUtil.email.util import CingTaEmail, BaseEmail, EmailTemplate
from django.core.mail import send_mail
from typing import List, Optional, Union, Type, Tuple

__all__ = ('CingTaEmail', 'BaseEmail', 'send_mail', 'EmailTemplate'
           'FuncCallBack')


def send_cingta_email(title: str,
                      to_email: List[str],
                      model: Optional[Type[EmailTemplate]] = None,
                      msg: Union[None, str] = None,
                      from_email_name: str = 'cingta',
                      attachments: List[Tuple[str, Union[str, bytes],
                                              Optional[str]]] = [],
                      **kwargs):
    mail: CingTaEmail = CingTaEmail(
        title,
        to_email,
        model,
        msg,
        from_email_name,
        attachments=attachments,
        **kwargs,
    )
    try:
        mail.send()
        return None
    except Exception as e:
        raise e
