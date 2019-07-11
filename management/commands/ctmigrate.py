from django.core.management.base import AppCommand
from django.core.management.commands.sqlmigrate import Command as SqlCommand
from typing import Dict, Optional
from datetime import datetime, date
import io
import os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing


def sql_format(raw_sql: str, app: str, migration_file: str):
    info: str = f"""
-- {app}_{migration_file}
{raw_sql}
--
"""
    return info


class Command(AppCommand):
    help = 'Write Sql From Django Migrate'

    def handle(self, *app_labels, **options):
        sqlmigrate_path: str = os.path.join(os.getcwd(), 'sql')
        if not os.path.exists(sqlmigrate_path):
            os.mkdir(sqlmigrate_path)

        data: Dict[date, List[str]] = {}

        for app in app_labels:
            app_sqlmigrate_path: str = os.path.join(sqlmigrate_path, app)
            app_migration_path: str = os.path.join(os.getcwd(), f'{app}/migrations')
            for root, _dir, files in os.walk(app_migration_path):
                for _file in files:
                    _file: str
                    if ('__' in _file) or (not _file.endswith('.py')):
                        continue
                    migration_file: str = os.path.join(root, _file)
                    _file_info: os.stat_result = os.stat(migration_file)
                    _file_datetime: datetime = datetime.fromtimestamp(_file_info.st_ctime)
                    with io.StringIO() as sio:
                        s = SqlCommand(stdout=sio)
                        argvs = ['-', '-', app, _file.split('.', 1)[0]]
                        s.run_from_argv(argvs)
                        raw_sql: str = sio.getvalue()

                    data_list: List[str] = data.setdefault(_file_datetime.date(), [])
                    data_list.append(sql_format(raw_sql, app, _file))

            if not os.path.exists(app_sqlmigrate_path):
                os.mkdir(app_sqlmigrate_path)

            for key, value in data.items():
                file_path: str = os.path.join(app_sqlmigrate_path, f'{format(_file_datetime, "%Y_%m_%d")}.sql')
                with open(file_path, 'w') as fp:
                    for v in value:
                        fp.write(f'{v}\n')