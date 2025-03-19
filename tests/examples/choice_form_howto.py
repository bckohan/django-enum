from .models.text_choices import TextChoicesExample
from django.forms import Form
from django_enum.forms import EnumChoiceField


class TextChoicesExampleForm(Form):

    color = EnumChoiceField(TextChoicesExample.Color)

    color_ext = EnumChoiceField(
        TextChoicesExample.Color,
        strict=False,
        choices=[
            ('P', 'Purple'),
            ('O', 'Orange'),
        ] + TextChoicesExample.Color.choices
    )


# when this form is rendered in a template it will include a selected
# option for the value 'Y' that is not part of our Color enumeration.
# since our field is not strict, we can set it to a value not in our
# enum or choice tuple.
form = TextChoicesExampleForm(
    initial={
        "color": TextChoicesExample.Color.RED,
        "color_ext": "Y"
    }
)
