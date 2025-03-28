from tests.examples.enums import Color, Permissions
from django.db import models
from django_enum import EnumField


class WidgetDemoStrict(models.Model):
    
    color = EnumField(Color, default=Color.RED)
    permissions = EnumField(Permissions)


class WidgetDemoNonStrict(models.Model):

    color = EnumField(Color, strict=False, max_length=12)
    permissions = EnumField(Permissions, strict=False)


class WidgetDemoRadiosAndChecks(WidgetDemoStrict):
    pass


class WidgetDemoRadiosAndChecksNulls(models.Model):

    color = EnumField(Color, default=None, null=True, blank=True)
    permissions = EnumField(Permissions, default=None, null=True, blank=True)


class WidgetDemoRadiosAndChecksNonStrict(WidgetDemoNonStrict):
    pass
