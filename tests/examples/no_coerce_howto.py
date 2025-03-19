from .models import NoCoerceExample


obj = NoCoerceExample()

# set to a valid EnumType value
obj.non_strict = '1'

# when accessed will be the primitive value
assert obj.non_strict == '1'
assert isinstance(obj.non_strict, str)
assert not isinstance(obj.non_strict, NoCoerceExample.EnumType)
