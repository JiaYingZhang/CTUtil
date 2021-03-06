from CTUtil.email.util import EmailTemplate
from django.core.management.base import BaseCommand
from CTUtil.email import send_cingta_email, BaseEmail
import os


def test_send_email(email: str):
    send_cingta_email(title='测试', to_email=[email], msg='测试发送邮件')


def test_send_trd_model(email: str):
    send_cingta_email(title='测试发送html', to_email=[email], model=SendTestEmail)


def test_send_att_email(email: str):
    send_cingta_email(
        title='测试发送附件',
        to_email=[email],
        model=SendTestEmail,
        attachments=[('测试.txt', b'dadasdasdadadasdaadadabfuafvuyafvua', None)])


class SendTestEmail(EmailTemplate):
    template: str = 'test.html'
    work_dir = os.path.dirname(os.path.dirname(__file__))


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-n', dest='name')
        parser.add_argument('-t',
                            dest='test',
                            action='store_true',
                            default=False)
        parser.add_argument('-m',
                            dest='nomal',
                            action='store_true',
                            default=False)
        parser.add_argument('-f',
                            dest='attachment',
                            action='store_true',
                            default=False)

    def handle(self, *args, **options):
        name: str = options.setdefault('name', '')
        if not name:
            raise ValueError('Not email to send')
        if options.setdefault('test'):
            test_send_trd_model(name)
        if options.setdefault('attachment'):
            test_send_att_email(name)
        if options.setdefault('nomal'):
            test_send_email(name)
