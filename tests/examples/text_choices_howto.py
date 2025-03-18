from .models import TextChoicesExample


obj = TextChoicesExample.objects.create(color=TextChoicesExample.Color.RED)

assert obj.color is TextChoicesExample.Color.RED
assert obj.color.label == 'Red'
assert obj.color.rgb == (1, 0, 0)
assert obj.color.hex == 'ff0000'

# enum-properties symmetric properties work as expected
assert obj.color == 'Red'
assert obj.color == (1, 0, 0)
assert obj.color == 'ff0000'
