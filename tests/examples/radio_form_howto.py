from .models.text_choices import TextChoicesExample
from django.forms import Form, RadioSelect
from django_enum.forms import EnumChoiceField, NonStrictRadioSelect


class TextChoicesExampleForm(Form):

    color = EnumChoiceField(TextChoicesExample.Color, widget=RadioSelect)
    
    # since this field is not strict, we can set it to a value not in our
    # enum or choice tuple.
    color_ext = EnumChoiceField(
        TextChoicesExample.Color,
        strict=False,
        choices=[
            ('P', 'Purple'),
            ('O', 'Orange'),
        ] + TextChoicesExample.Color.choices,
        widget=NonStrictRadioSelect
    )


# when this form is rendered in a template it will include a selected
# option for the value 'Y' that is not part of our Color enumeration.
form = TextChoicesExampleForm(
    initial={
        "color": TextChoicesExample.Color.RED,
        "color_ext": "Y"
    }
)
