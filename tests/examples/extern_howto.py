from .models.extern import ExternalChoices

assert ExternalChoices._meta.get_field('txt_enum1').choices == [
    ('V0', 'VALUE0'),
    ('V1', 'VALUE1'),
    ('V2', 'VALUE2')
]

assert ExternalChoices._meta.get_field('txt_enum2').choices == [
    ('V0', 'Value0'),
    ('V1', 'Value1'),
    ('V2', 'Value2')
]
