from .models import TextChoicesExample

from django_enum.drf import EnumField
from rest_framework import serializers


class ExampleSerializer(serializers.Serializer):

    color = EnumField(TextChoicesExample.Color)


ser = ExampleSerializer(data={'color': (1, 0, 0)})
assert ser.is_valid()
