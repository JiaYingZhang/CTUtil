from field import JsTimeStampField, Form, CharField, IntField
from valid_func import maxlength, minlength


class TestForm(Form):
    datetime = JsTimeStampField('starttime')
    name = CharField('name', maxlength(4))
    id = IntField('id')
    univ = CharField('univ', minlength(3))

t = TestForm({'datetime': '1565659297000', 'name': '12345', 'id': '1', 'univ': '12'})
t.is_valid()
print(t.error)
print(t.backend)