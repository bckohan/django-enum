==========
Change Log
==========

v2.0.0
======

* Implemented `Supply a mixin for DRF ModelSerializers that instantiates the provided DRF EnumField type for model EnumFields. <https://github.com/bckohan/django-enum/issues/47>`_
* Implemented `Add support for date, datetime and timedelta enumeration types. <https://github.com/bckohan/django-enum/issues/43>`_
* Implemented `EnumField's should inherit from common base titled EnumField <https://github.com/bckohan/django-enum/issues/46>`_
* Implemented `Provide parameter to override integer range on EnumField. <https://github.com/bckohan/django-enum/issues/38>`_
* Implemented `Add all official supported Django RDBMS backends to CI <https://github.com/bckohan/django-enum/issues/33>`_
* Fixed `to_python() raises ValueError instead of spec'ed ValidationError <https://github.com/bckohan/django-enum/issues/44>`_
* Fixed `When coerce is false, to_python does not convert to the Enum's primitive type <https://github.com/bckohan/django-enum/issues/39>`_
* Fixed `None should be an allowable enumeration value in enums of any primitive type. <https://github.com/bckohan/django-enum/issues/42>`_

v1.2.1
======

* Fixed `Document that with version 1.4 of enum-properties label is no longer overridable for Choices <https://github.com/bckohan/django-enum/issues/37>`_

v1.2.0
======

* Implemented `Compat for enums not deriving from Django's choices. <https://github.com/bckohan/django-enum/issues/34>`_


v1.1.2
======

* Fixed `LICENSE packaged into source dir. <https://github.com/bckohan/django-enum/issues/23>`_

v1.1.1
======

* Fixed `Broken on Django4.1/Python 3.11. <https://github.com/bckohan/django-enum/issues/17>`_

v1.1.0
======

* Fixed `django-filter intergration for non-strict values does not work. <https://github.com/bckohan/django-enum/issues/6>`_
* Implemented `Set EnumChoiceField to the default form field type. <https://github.com/bckohan/django-enum/issues/5>`_
* Implemented `Coerce default values to Enum types. <https://github.com/bckohan/django-enum/issues/4>`_
* Implemented `Use custom descriptor to coerce fields to Enum type on assignment. <https://github.com/bckohan/django-enum/issues/3>`_

v1.0.1
======

* Fix dependency issue - allow python 3.6


v1.0.0
======

* Initial Re-Release (production/stable)


v0.1.0
======

* Legacy django-enum library maintained by `Jacob Smullyan <https://pypi.org/user/smulloni>`_. Source located `here <https://github.com/smulloni/django-enum-old>`_.
