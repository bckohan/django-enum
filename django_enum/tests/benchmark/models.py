from django.db.models import Model, BooleanField, Index
from django_enum.tests.benchmark.enums import enums
from django_enum import EnumField


def chop(original_list, limit=32):
    return [original_list[i:i+limit] for i in range(0, len(original_list), limit)]


for num_flags in range(0, 63):
    globals()[f'FlagTester{num_flags:03d}'] = type(
        f'FlagTester{num_flags:03d}',
        (Model,),
        {
            f'flags': EnumField(enums[num_flags]),
            '__module__': 'django_enum.tests.benchmark.models',
            'FLAG': True,
            'num_flags': num_flags+1
        }
    )

    globals()[f'BoolTester{num_flags:03d}'] = type(
        f'BoolTester{num_flags:03d}',
        (Model,),
        {
            **{
                f'flg_{flg}': BooleanField()
                for flg in range(0, num_flags+1)
            },
            '__module__': 'django_enum.tests.benchmark.models',
            'BOOL': True,
            'num_flags': num_flags+1,
            'Meta': type(
                'Meta',
                (),
                {
                    'indexes': [
                        Index(fields=[
                            f'flg_{flg}' for flg in flgs
                        ]) for flgs in chop(range(num_flags+1))
                    ]
                })
        }
    )
