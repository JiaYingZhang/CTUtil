from typing import Dict, Union, List
import os
from jinja2 import Environment, select_autoescape, FileSystemLoader
from CTUtil.types import EmailTypes

_BASE_FILE = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    loader=FileSystemLoader(os.path.join(_BASE_FILE, 'template')),
    auto_reload=select_autoescape(['html', 'xml']))
template = env.get_template('email_bug.html')

_NEED = '需求'
_BUG = 'BUG'
ZHAOPING = '招聘'


class CingTaEmail(object):

    SENED_EMAIL: str = '{name} <service@cingta.com>'

    def __init__(self,
                 title: str,
                 to_email: List[str],
                 model: Union[str, None]=None,
                 msg: Union[str, None]=None,
                 from_email_name: str='cingta',
                 **kwargs) -> None:

        self.SENED_EMAIL = self.SENED_EMAIL.format(name=from_email_name)
        if msg is None:
            self.msg: str = ''
        else:
            self.msg: str = msg

        self.to_email: List[str] = to_email

        if model is None:
            self._html_model: str = _NEED
        else:
            self._html_model: str = model
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
        html_text = self.kwargs.get('html_string')
        if html_text:
            return html_text
        return self._set_model_template.render(**self.kwargs)

    @property
    def _set_model_template(self) -> str:
        _d: Dict[str, str] = {
            _NEED: env.get_template('email_need.html'),
            _BUG: env.get_template('email_bug.html'),
            ZHAOPING: env.get_template('email_zhaoping.html')
        }
        if self._html_model not in _d.keys():
            raise ValueError('not this html model')
        template: str = _d.get(self._html_model)
        return template

    def __unicode__(self) -> str:
        return 'send email {} to {}'.format(
            self.SUBJECT_STRING,
            self.email, )

