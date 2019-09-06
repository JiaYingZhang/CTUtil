from django.test import TestCase
from typing import Any
import json
import yaml


class CingtaTest(TestCase):

    @classmethod
    def load_test_data(cls, file_name: str) -> Any:
        with open(file_name, 'r', encoding='utf8') as f:
            data: str = f.read()
        if file_name.endswith('json'):
            return json.loads(data)
        elif file_name.endswith('yaml') or file_name.endswith('yml'):
            return yaml.load(data)
        else:
            return data