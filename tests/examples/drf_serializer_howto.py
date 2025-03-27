from .models import TextChoicesExample, Constellation

from django_enum.drf import EnumField, FlagField
from rest_framework import serializers


class ExampleSerializer(serializers.Serializer):

    color = EnumField(TextChoicesExample.Color)
    
    # from the flags tutorial
    constellation = FlagField(Constellation)


ser = ExampleSerializer(
    data={
        'color': (1, 0, 0),
        'constellation': [
            Constellation.GALILEO.name,
            Constellation.GPS.name
        ]
    }
)
assert ser.is_valid()
