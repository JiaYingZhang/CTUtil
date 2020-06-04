from typing import Dict, Union, List, Type, Tuple, Optional
import os
from jinja2 import Environment, select_autoescape, FileSystemLoader
from django.core.mail import EmailMultiAlternatives


class ProcessEmail(type):
    manage: set = set()

    def __new__(cls, clsname, bases, clsdict):
        _type = type(clsname, bases, clsdict)
        cls.manage.add(_type)
        return _type


class BaseEmail(metaclass=ProcessEmail):
    template: str = ''
    work_dir: str = os.getcwd()
    template_dir: Optional[str] = None

    @classmethod
    def render(cls, *args, **kwargs):
        if not cls.template:
            return ''
        loader_dir = [
            os.path.join(cls.work_dir, 'template'),
            os.path.join(cls.work_dir, 'templates'),
        ]
        if cls.template_dir:
            loader_dir.append(cls.template_dir)
        _env = Environment(loader=FileSystemLoader(loader_dir),
                           auto_reload=select_autoescape(['html', 'xml']))
        template = _env.get_template(cls.template).render(**kwargs)
        return template


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
                 attachments: List[Tuple[str, Union[str, bytes],
                                         Optional[str]]] = [],
                 **kwargs) -> None:

        self.SENED_EMAIL = self.SENED_EMAIL.format(name=from_email_name)
        self.msg: str = msg if msg else ''
        self.to_email: List[str] = to_email
        self.template: Optional[Type[EmailTemplate]] = model
        self.title = title
        self.kwargs: Dict[str, str] = kwargs
        self.attachments = attachments

        self.email_message = EmailMultiAlternatives(
            subject=title,
            body=msg,
            from_email=self.SENED_EMAIL,
            to=to_email,
        )

    def get_html_text(self) -> str:
        if 'html' in self.kwargs:
            html_text = self.kwargs.setdefault('html_string', '')
            return html_text
        elif self.template:
            return self.template.render(**self.kwargs)
        else:
            raise EmailContentError

    def process_email(self):
        html_text = self.get_html_text()
        if html_text:
            self.email_message.attach_alternative(html_text, 'text/html')

        # 当body为空并且有附件是情况下 不显示html
        if not self.email_message.body:
            self.email_message.body = '青塔'
        for name, content, _ in self.attachments:
            self.email_message.attach(name, content, _)

    def __unicode__(self) -> str:
        return f'send email: {self.SENED_EMAIL} to {self.to_email}'

    def send(self):
        self.process_email()
        self.email_message.send()
