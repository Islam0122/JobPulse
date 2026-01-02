import django_filters
from .models import RequiredChannel


class RequiredChannelFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = RequiredChannel
        fields = ("is_active",)
