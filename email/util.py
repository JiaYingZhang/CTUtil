from typing import Dict, Union, List, Type
import os
from jinja2 import Environment, select_autoescape, FileSystemLoader
from CTUtil.types import EmailTypes

_BASE_FILE = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    loader=FileSystemLoader(os.path.join(_BASE_FILE, 'template')),
    auto_reload=select_autoescape(['html', 'xml']))


class CingTaEmail(object):

    SENED_EMAIL: str = '{name} <service@cingta.com>'

    def __init__(self,
                 title: str,
                 to_email: List[str],
                 model: Type[EmailTypes]=EmailTypes.DEMAND,
                 msg: Union[str, None]=None,
                 from_email_name: str='cingta',
                 **kwargs) -> None:

        self.SENED_EMAIL = self.SENED_EMAIL.format(name=from_email_name)
        self.msg: str = msg if msg else ''

        self.to_email: List[str] = to_email
        self._html_model: Type[EmailTypes] = model
        self.title = title
        self.kwargs: Dict[str, str] = kwargs

    def _make_email_text(self) -> str:
        text = """{msg}""".format(msg=self.msg)
        return text

    @property
    def email_msg(self) -> Dict[str, str]:
        data = {
            'subject': self.title,
            'message': self._make_email_text(),
            'from_email': self.SENED_EMAIL,
            'recipient_list': self.to_email,
            'html_message': self._html_text() if not self.msg else None,
        }
        return data

    def _html_text(self) -> str:
        html_text = self.kwargs.setdefault('html_string', '')
        if html_text:
            return html_text
        template = env.get_template(self._set_model_template).render(**self.kwargs)
        return template

    @property
    def _set_model_template(self) -> str:
        email_type_mapping_template: Dict[Type[EmailTypes], str] = {
            EmailTypes.DEMAND: 'email_need.html',
            EmailTypes.BUG: 'email_bug.html',
            EmailTypes.RECRUIT: 'email_zhaoping.html',
            EmailTypes.REGISTER: 'email_register.html',
        }
        if self._html_model not in email_type_mapping_template.keys():
            raise ValueError('not this html model')
        template: str = email_type_mapping_template.setdefault(self._html_model)
        return template

    def __unicode__(self) -> str:
        return 'send email: {} to {}'.format(
            self.SUBJECT_STRING,
            self.email, )
