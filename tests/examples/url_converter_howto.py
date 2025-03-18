from django.urls import reverse
from tests.examples.urls import Enum1


assert reverse("examples:enum_default", kwargs={"enum": Enum1.A}) == "/1"
assert reverse("examples:enum_default", kwargs={"enum": Enum1.B}) == "/2"

assert reverse("examples:enum_by_name", kwargs={"enum": Enum1.A}) == "/A"
assert reverse("examples:enum_by_name", kwargs={"enum": Enum1.B}) == "/B"
