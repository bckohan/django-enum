from .models import TextChoicesExample
from django_enum.filters import FilterSet as EnumFilterSet
from django_filters.views import FilterView


class TextChoicesExampleFilterViewSet(FilterView):

    class TextChoicesExampleFilter(EnumFilterSet):
        class Meta:
            model = TextChoicesExample
            fields = '__all__'

    filterset_class = TextChoicesExampleFilter
    model = TextChoicesExample
