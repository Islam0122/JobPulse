from rest_framework.generics import CreateAPIView
from .serializers import CommentCreateSerializer


class CommentCreateView(CreateAPIView):
    serializer_class = CommentCreateSerializer
