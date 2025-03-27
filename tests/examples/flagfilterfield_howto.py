from .models import Constellation, GNSSReceiver
from django_enum.filters import EnumFlagFilter
from django_filters.views import FilterView
from django_filters import FilterSet


class FlagExampleFilterViewSet(FilterView):

    class FlagExampleFilter(FilterSet):

        constellation = EnumFlagFilter(enum=Constellation)

        class Meta:
            model = GNSSReceiver
            fields = '__all__'

    filterset_class = FlagExampleFilter
    model = GNSSReceiver

# now filtering by flags works:
# e.g.:  /?constellation=GPS&constellation=GLONASS
