import pytest

pytest.importorskip("enum_properties")

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from tests.utils import DJANGO_FILTERS, DJANGO_REST_FRAMEWORK


class ExampleTests(TestCase):  # pragma: no cover  - why is this necessary?
    def test_readme(self):
        from tests.enum_prop.models import MyModel

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

    def test_mapboxstyle(self):
        from tests.examples import mapbox_tutorial
        from tests.examples.models.mapbox import Map

        map_obj = Map.objects.create()

        self.assertTrue(map_obj.style.uri == "mapbox://styles/mapbox/streets-v12")

        # uri's are symmetric
        map_obj.style = "mapbox://styles/mapbox/light-v11"
        self.assertTrue(map_obj.style == Map.MapBoxStyle.LIGHT)
        self.assertTrue(map_obj.style == 3)
        self.assertTrue(map_obj.style == "light")

        # so are labels (also case insensitive)
        map_obj.style = "satellite streets"
        self.assertTrue(map_obj.style == Map.MapBoxStyle.SATELLITE_STREETS)

        # when used in API calls (coerced to strings) - they "do the right
        # thing"
        self.assertTrue(
            str(map_obj.style) == "mapbox://styles/mapbox/satellite-streets-v12"
        )

    def test_properties(self):
        from tests.examples import properties_example
        from tests.examples.models import PropertyExample

        PropertyExample.objects.all().delete()

        instance = PropertyExample.objects.create(color=PropertyExample.Color("FF0000"))
        self.assertTrue(
            instance.color
            == PropertyExample.Color("RED")
            == PropertyExample.Color("R")
            == PropertyExample.Color((1, 0, 0))
        )

        # direct comparison to any symmetric value also works
        self.assertTrue(instance.color == "FF0000")
        self.assertFalse(instance.color == "Red")
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
            PropertyExample.objects.filter(color=PropertyExample.Color.RED).first()
            == instance
        )

        self.assertTrue(
            PropertyExample.objects.filter(color=(1, 0, 0)).first() == instance
        )

        self.assertTrue(
            PropertyExample.objects.filter(color="FF0000").first() == instance
        )

        from django_enum.forms import EnumChoiceField

        class PropertyExampleForm(ModelForm):
            color = EnumChoiceField(PropertyExample.Color)

            class Meta:
                model = PropertyExample
                fields = "__all__"

        # this is possible
        form = PropertyExampleForm({"color": "FF0000"})
        form.save()
        self.assertTrue(form.instance.color == PropertyExample.Color.RED)

    def test_properties_with_choices(self):
        from tests.examples.models import ChoicesWithProperties

        ChoicesWithProperties.objects.all().delete()

        instance = ChoicesWithProperties.objects.create(
            color=ChoicesWithProperties.Color("FF0000")
        )
        self.assertTrue(
            instance.color
            == ChoicesWithProperties.Color("Red")
            == ChoicesWithProperties.Color("R")
            == ChoicesWithProperties.Color((1, 0, 0))
        )

        # direct comparison to any symmetric value also works
        self.assertTrue(instance.color == "FF0000")
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
            ChoicesWithProperties.objects.filter(
                color=ChoicesWithProperties.Color.RED
            ).first()
            == instance
        )

        self.assertTrue(
            ChoicesWithProperties.objects.filter(color=(1, 0, 0)).first() == instance
        )

        self.assertTrue(
            ChoicesWithProperties.objects.filter(color="FF0000").first() == instance
        )

        from django_enum.forms import EnumChoiceField

        class ChoicesWithPropertiesForm(ModelForm):
            color = EnumChoiceField(ChoicesWithProperties.Color)

            class Meta:
                model = ChoicesWithProperties
                fields = "__all__"

        # this is possible
        form = ChoicesWithPropertiesForm({"color": "FF0000"})
        form.save()
        self.assertTrue(form.instance.color == ChoicesWithProperties.Color.RED)

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
        from tests.examples import basic_example
        from tests.examples.models import BasicExample

        instance = BasicExample.objects.create(
            txt_enum=BasicExample.TextEnum.VALUE1,
            int_enum=3,  # by-value assignment also works
        )

        self.assertTrue(instance.txt_enum == BasicExample.TextEnum("V1"))
        self.assertTrue(instance.txt_enum.label == "Value 1")

        self.assertTrue(instance.int_enum == BasicExample.IntEnum["THREE"])
        self.assertTrue(instance.int_enum.value == 3)

        self.assertRaises(
            ValueError, BasicExample.objects.create, txt_enum="AA", int_enum=3
        )

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

    def test_flag_readme_ex(self):
        from tests.examples.models import FlagExample
        from tests.examples.models.flag import Permissions
        from tests.examples import flag_example

        FlagExample.objects.create(
            permissions=Permissions.READ | Permissions.WRITE,
        )

        FlagExample.objects.create(
            permissions=Permissions.READ | Permissions.EXECUTE,
        )

        self.assertEqual(
            FlagExample.objects.count(),
            3,
        )

        self.assertEqual(
            FlagExample.objects.filter(
                permissions__has_all=Permissions.READ | Permissions.WRITE
            ).count(),
            2,
        )

        self.assertEqual(
            FlagExample.objects.filter(
                permissions__has_all=Permissions.EXECUTE
            ).count(),
            2,
        )

    def test_mixed_value(self):
        from tests.examples import mixed_value_example

    def test_path_value(self):
        from tests.examples import path_value_example

    def test_custom_value(self):
        from tests.examples import custom_value_example

    def test_gnss_tutorial(self):
        from tests.examples import gnss_tutorial

    def test_gnss_tutorial_vanilla(self):
        from tests.examples import gnss_vanilla_tutorial

    def test_equivalency_howto(self):
        from tests.examples import equivalency_howto

    def test_extern_howto(self):
        from tests.examples import extern_howto

    def test_urls_howto(self):
        from tests.examples import url_converter_howto

        self.assertEqual(self.client.get("/A").content.decode(), "enum=<Enum1.A: 1>")
        self.assertEqual(self.client.get("/B").content.decode(), "enum=<Enum1.B: 2>")
        self.assertEqual(self.client.get("/1").content.decode(), "enum=<Enum1.A: 1>")
        self.assertEqual(self.client.get("/2").content.decode(), "enum=<Enum1.B: 2>")

    def test_text_choices_howto(self):
        from tests.examples import text_choices_howto

    @pytest.mark.skipif(not DJANGO_REST_FRAMEWORK, reason="DRF not installed")
    def test_drf_serializer_howto(self):
        from tests.examples import drf_serializer_howto

    def _filterset_webcheck(self, name):
        from tests.examples.models import TextChoicesExample
        from django.urls import reverse
        from playwright.sync_api import sync_playwright

        TextChoicesExample.objects.create(color=TextChoicesExample.Color.RED)
        TextChoicesExample.objects.create(color=TextChoicesExample.Color.BLUE)
        TextChoicesExample.objects.create(color=TextChoicesExample.Color.GREEN)

        url = reverse(name)

        red_content = self.client.get(f"{url}?color=ReD").content.decode()
        green_content = self.client.get(f"{url}?color=00Ff00").content.decode()
        blue_content = self.client.get(f"{url}?color=B").content.decode()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            page.set_content(red_content)
            list_items = page.locator("ul li").all_text_contents()
            self.assertTrue("Red" in list_items)
            self.assertFalse("Green" in list_items)
            self.assertFalse("Blue" in list_items)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Red"
            )

            page.set_content(green_content)
            list_items = page.locator("ul li").all_text_contents()
            self.assertFalse("Red" in list_items)
            self.assertTrue("Green" in list_items)
            self.assertFalse("Blue" in list_items)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Green"
            )

            page.set_content(blue_content)
            list_items = page.locator("ul li").all_text_contents()
            self.assertFalse("Red" in list_items)
            self.assertFalse("Green" in list_items)
            self.assertTrue("Blue" in list_items)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Blue"
            )

            browser.close()

    @pytest.mark.skipif(not DJANGO_FILTERS, reason="django-filters not installed")
    def test_filterfield_howto(self):
        from tests.examples import filterfield_howto

        self._filterset_webcheck("howto:filterfield")

    @pytest.mark.skipif(not DJANGO_FILTERS, reason="django-filters not installed")
    def test_filterset_howto(self):
        from tests.examples import filterset_howto

        self._filterset_webcheck("howto:filterset")

    def test_flag_howto(self):
        from tests.examples import flag_howto

    def test_choice_form_howto(self):
        from tests.examples import choice_form_howto
        from django.urls import reverse
        from playwright.sync_api import sync_playwright

        url = reverse("howto_forms:choice")

        initial_content = self.client.get(url).content.decode()

        response = self.client.post(url, {"color": "00FF00", "color_ext": "P"})
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["color"], choice_form_howto.TextChoicesExample.Color.GREEN
        )
        self.assertEqual(form.cleaned_data["color_ext"], "P")
        post_green_purple_content = response.content.decode()

        response = self.client.post(url, {"color": "BlUe", "color_ext": "X"})
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["color"], choice_form_howto.TextChoicesExample.Color.BLUE
        )
        self.assertEqual(form.cleaned_data["color_ext"], "X")
        post_blue_x_content = response.content.decode()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            page.set_content(initial_content)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Red"
            )
            self.assertEqual(
                page.locator("select#id_color_ext option:checked").text_content(), "Y"
            )

            page.set_content(post_green_purple_content)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Green"
            )
            self.assertEqual(
                page.locator("select#id_color_ext option:checked").text_content(),
                "Purple",
            )

            page.set_content(post_blue_x_content)
            self.assertEqual(
                page.locator("select#id_color option:checked").text_content(), "Blue"
            )
            self.assertEqual(
                page.locator("select#id_color_ext option:checked").text_content(), "X"
            )

        with self.assertRaises(ValidationError):
            response = self.client.post(url, {"color": "X", "color_ext": "G"})

    def test_flag_form_howto(self):
        # TODO
        pass

    def test_strict_example(self):
        from tests.examples import strict_howto

    def test_no_coerce_example(self):
        from tests.examples import no_coerce_howto
