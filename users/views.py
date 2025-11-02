from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer, TelegramLinkSerializer
from .models import TelegramUser


class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LinkTelegramAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TelegramLinkSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_id = serializer.validated_data["chat_id"]

        if not chat_id:
            return Response({"error": "chat_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        telegram_user, created = TelegramUser.objects.get_or_create(user=request.user, defaults={"chat_id": chat_id})

        if not created:
            telegram_user.chat_id = chat_id
            telegram_user.save()

        return Response({"status": "success", "message": f"Telegram chat_id {chat_id} linked to your account"})
