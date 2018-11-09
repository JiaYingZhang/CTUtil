import os
work_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
sys.path.append(work_path)
os.chdir(work_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "new_cingtaweb.settings")
from utils.email import send_cingta_email
from utils.email.util import ZHAOPING


def test_send_zhaobing_email():
    send_cingta_email(title='您有新的消息', model=ZHAOPING, to_email=['zhangjiaying121@163.com'], from_email_name='kaka')


def main():
    test_send_zhaobing_email()


if __name__ == '__main__':
    main()