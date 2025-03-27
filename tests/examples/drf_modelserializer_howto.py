from .models import TextChoicesExample

from django_enum.drf import EnumFieldMixin
from rest_framework import serializers


class ExampleModelSerializer(EnumFieldMixin, serializers.Serializer):

    class Meta:
        model = TextChoicesExample


ser = ExampleModelSerializer(
    data={
        'color': (1, 0, 0),
    }
)
assert ser.is_valid()
