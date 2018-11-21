from typing import Dict, Any, List


def parse_multiple_key(data: Dict[Any, Any],
                       key_string: str,
                       split_word: str='.',
                       deepest: int=5):
    keys_list: List[str] = key_string.split(split_word)
    if not keys_list:
        raise TypeError('Keys_string: key1.key2.key3')
    if len(keys_list) > deepest:
        raise TypeError('Too much keys')
    if len(keys_list) == 1:
        return data.setdefault(keys_list[0], None)
    else:
        first_key: str = keys_list[0]
        data: Dict[Any, Any] = data.setdefault(first_key, {})
        if not data:
            return
        else:
            return parse_multiple_key(
                data,
                '.'.join(keys_list[1:]),
                split_word=split_word,
                deepest=deepest - 1)


class CingtaSerialize(object):
    model = None
    exclude = []

    @classmethod
    def get_need_fieldname(cls):
        fields = []
        for field in cls.model._meta.get_fields():
            if field.name not in cls.exclude:
                fields.append(field.name)
        return fields

    @classmethod
    def queryset_to_json(cls, qs):
        _d = {}
        if qs:
            for name in cls.get_need_fieldname():
                value = getattr(qs, name)
                if value:
                    _d[name] = str(value)
                else:
                    _d[name] = ''
        return _d