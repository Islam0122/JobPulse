from rest_framework.generics import ListAPIView
from .models import RequiredChannel
from .serializers import RequiredChannelSerializer
from .filters import RequiredChannelFilter


class RequiredChannelListAPIView(ListAPIView):
    serializer_class = RequiredChannelSerializer
    filterset_class = RequiredChannelFilter

    def get_queryset(self):
        return RequiredChannel.objects.filter(is_active=True)
