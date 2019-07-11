from jinja2 import Environment, select_autoescape, FileSystemLoader, Template
from django.core.management.base import BaseCommand

import os
import multiprocessing


BASE_FILE = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_FILE, 'config')),
    auto_reload=select_autoescape(['conf', 'ini']))


class Command(BaseCommand):
    help = """
        -p: port uwsgi项目端口
        -w: worker uwsgi工作进程
        -wp: worker_path 工作目录
        -s: server_name nginx server_name
        -kp: key_path nginx https 密钥路径
        --https: 是否https
    """

    def add_arguments(self, parser):
        parser.add_argument('-p', dest='port', default=8000)
        parser.add_argument('-w', dest='worker', default=multiprocessing.cpu_count())
        parser.add_argument('-wp', dest='work_path', default=os.getcwd())
        parser.add_argument('-s', dest='server_name', default='')
        parser.add_argument('-kp', dest='key_path', default='')
        parser.add_argument(
            '--https', dest='ishttps', action='store_true', default=False)

    def handle(self, *args, **options):
        project: str = os.getcwd().split('/')[-1]
        port: str = options.setdefault('port')
        options: dict
        uwsgi_string: str = env.get_template('uwsgi.ini').render(
            port=port,
            worker=options.setdefault('worker'),
            workpath=options.setdefault('work_path'),
            project=project,
        )

        if options.setdefault('ishttps'):
            listen: str = '443'
            nginx_template: Template = env.get_template('nginx_https.conf')
        else:
            listen = '80'
            nginx_template: Template = env.get_template('nginx.conf')
        nginx_string: str = nginx_template.render(
            listen=listen,
            server_name=options.setdefault('server_name'),
            port=port,
            key_path=options.setdefault('key_path'),
        )

        conf_path: str = os.path.join(os.getcwd(), 'conf')
        if not os.path.exists(conf_path):
            os.mkdir(conf_path)

        with open(os.path.join(conf_path, f'{project}_uwsgi.ini'), 'w') as fp:
            fp.write(uwsgi_string)

        with open(os.path.join(conf_path, f'{project}_nginx.conf'), 'w') as fp:
            fp.write(nginx_string)
