from .models import StrictExample


obj = StrictExample()

# set to a valid EnumType value
obj.non_strict = '1'
# when accessed will be an EnumType instance
assert obj.non_strict is StrictExample.EnumType.ONE

# we can also store any string less than or equal to length 10
obj.non_strict = 'arbitrary'
obj.full_clean()  # no errors
# when accessed will be a str instance
assert obj.non_strict == 'arbitrary'
