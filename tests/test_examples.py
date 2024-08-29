import pytest

pytest.importorskip("enum_properties")

from django.test import TestCase

from tests.enum_prop.models import MyModel
from django.core.exceptions import ValidationError
from django.forms import ModelForm


class TestExamples(TestCase):
    def test_readme(self):
        instance = MyModel.objects.create(
            txt_enum=MyModel.TextEnum.VALUE1,
            int_enum=3,  # by-value assignment also works
            color=MyModel.Color("FF0000"),
        )

        self.assertEqual(instance.txt_enum, MyModel.TextEnum("V1"))
        self.assertEqual(instance.txt_enum.label, "Value 1")

        self.assertEqual(instance.int_enum, MyModel.IntEnum["THREE"])

        instance.full_clean()
        self.assertEqual(instance.int_enum.value, 3)

        self.assertEqual(instance.color, MyModel.Color("Red"))
        self.assertEqual(instance.color, MyModel.Color("R"))
        self.assertEqual(instance.color, MyModel.Color((1, 0, 0)))

        # save back by any symmetric value
        instance.color = "FF0000"
        instance.full_clean()
        instance.save()

        self.assertEqual(instance.color.hex, "ff0000")

    """
    # Django breaks auto
    def test_auto_enum(self):
        from django_enum import IntegerChoices
        from enum import auto

        class AutoEnum(IntegerChoices):
            ONE = auto(), 'One'
            TWO = auto(), 'Two'
            THREE = auto(), 'Three'
    """


class ExampleTests(TestCase):  # pragma: no cover  - why is this necessary?
    def test_mapboxstyle(self):
        from tests.examples.models import Map

        map_obj = Map.objects.create()

        self.assertTrue(map_obj.style.uri == "mapbox://styles/mapbox/streets-v11")

        # uri's are symmetric
        map_obj.style = "mapbox://styles/mapbox/light-v10"
        self.assertTrue(map_obj.style == Map.MapBoxStyle.LIGHT)
        self.assertTrue(map_obj.style == 3)
        self.assertTrue(map_obj.style == "light")

        # so are labels (also case insensitive)
        map_obj.style = "satellite streets"
        self.assertTrue(map_obj.style == Map.MapBoxStyle.SATELLITE_STREETS)

        # when used in API calls (coerced to strings) - they "do the right
        # thing"
        self.assertTrue(
            str(map_obj.style) == "mapbox://styles/mapbox/satellite-streets-v11"
        )

    def test_color(self):
        from tests.examples.models import TextChoicesExample

        instance = TextChoicesExample.objects.create(
            color=TextChoicesExample.Color("FF0000")
        )
        self.assertTrue(
            instance.color
            == TextChoicesExample.Color("Red")
            == TextChoicesExample.Color("R")
            == TextChoicesExample.Color((1, 0, 0))
        )

        # direct comparison to any symmetric value also works
        self.assertTrue(instance.color == "Red")
        self.assertTrue(instance.color == "R")
        self.assertTrue(instance.color == (1, 0, 0))

        # save by any symmetric value
        instance.color = "FF0000"

        # access any property right from the model field
        self.assertTrue(instance.color.hex == "ff0000")

        # this also works!
        self.assertTrue(instance.color == "ff0000")

        # and so does this!
        self.assertTrue(instance.color == "FF0000")

        instance.save()

        self.assertTrue(
            TextChoicesExample.objects.filter(
                color=TextChoicesExample.Color.RED
            ).first()
            == instance
        )

        self.assertTrue(
            TextChoicesExample.objects.filter(color=(1, 0, 0)).first() == instance
        )

        self.assertTrue(
            TextChoicesExample.objects.filter(color="FF0000").first() == instance
        )

        from django_enum import EnumChoiceField

        class TextChoicesExampleForm(ModelForm):
            color = EnumChoiceField(TextChoicesExample.Color)

            class Meta:
                model = TextChoicesExample
                fields = "__all__"

        # this is possible
        form = TextChoicesExampleForm({"color": "FF0000"})
        form.save()
        self.assertTrue(form.instance.color == TextChoicesExample.Color.RED)

    def test_strict(self):
        from tests.examples.models import StrictExample

        obj = StrictExample()

        # set to a valid EnumType value
        obj.non_strict = "1"
        # when accessed will be an EnumType instance
        self.assertTrue(obj.non_strict is StrictExample.EnumType.ONE)

        # we can also store any string less than or equal to length 10
        obj.non_strict = "arbitrary"
        obj.full_clean()  # no errors
        # when accessed will be a str instance
        self.assertTrue(obj.non_strict == "arbitrary")

    def test_basic(self):
        from tests.examples.models import MyModel

        instance = MyModel.objects.create(
            txt_enum=MyModel.TextEnum.VALUE1,
            int_enum=3,  # by-value assignment also works
        )

        self.assertTrue(instance.txt_enum == MyModel.TextEnum("V1"))
        self.assertTrue(instance.txt_enum.label == "Value 1")

        self.assertTrue(instance.int_enum == MyModel.IntEnum["THREE"])
        self.assertTrue(instance.int_enum.value == 3)

        self.assertRaises(ValueError, MyModel.objects.create, txt_enum="AA", int_enum=3)

        instance.txt_enum = "AA"
        self.assertRaises(ValidationError, instance.full_clean)

    def test_no_coerce(self):
        from tests.examples.models import NoCoerceExample

        obj = NoCoerceExample()
        # set to a valid EnumType value
        obj.non_strict = "1"
        obj.full_clean()

        # when accessed from the db or after clean, will be the primitive value
        self.assertTrue(obj.non_strict == "1")
        self.assertTrue(isinstance(obj.non_strict, str))
        self.assertFalse(isinstance(obj.non_strict, NoCoerceExample.EnumType))
