from typing import Dict, Union, List, Type, Set
import os
from jinja2 import Environment, select_autoescape, FileSystemLoader


class ProcessEmail(type):
    manage: set = set()

    def __new__(cls, clsname, bases, clsdict):
        _type = type(clsname, bases, clsdict)
        cls.manage.add(_type)
        return _type


class BaseEmail(metaclass=ProcessEmail):
    template: str = ''
    work_dir: str = os.getcwd()


class EmailTemplate(BaseEmail):
    pass


class EmailContentError(Exception):
    "msg, html_string and html_model in the parameter cannot be empty at the same time"


class CingTaEmail(object):

    SENED_EMAIL: str = '{name} <service@cingta.com>'

    def __init__(self,
                 title: str,
                 to_email: List[str],
                 model: Type[EmailTemplate] = None,
                 msg: Union[str, None] = None,
                 from_email_name: str = 'cingta',
                 **kwargs) -> None:

        self.SENED_EMAIL = self.SENED_EMAIL.format(name=from_email_name)
        self.msg: str = msg if msg else ''

        self.to_email: List[str] = to_email
        self._html_model: Type[EmailTemplate] = model
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
            'html_message': self._html_text(),
        }
        return data

    def _html_text(self) -> str:
        if self.msg:
            return self.msg
        elif 'html' in self.kwargs:
            html_text = self.kwargs.setdefault('html_string', '')
            return html_text
        elif self._html_model:
            _env = Environment(loader=FileSystemLoader(
                os.path.join(self._html_model.work_dir, 'template')),
                               auto_reload=select_autoescape(['html', 'xml']))
            template = _env.get_template(
                self._html_model.template).render(**self.kwargs)
            return template
        else:
            raise EmailContentError

    def __unicode__(self) -> str:
        return 'send email: {} to {}'.format(
            self.SUBJECT_STRING,
            self.email,
        )
