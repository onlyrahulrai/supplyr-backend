from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from dj_rest_auth.views import LoginView

from .serializers import UserDetailsSerializer

User = get_user_model()

class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserDetailsSerializer(user)
        return Response(serializer.data)


class CustomLoginView(LoginView):
    def get_response(self):
        response = super().get_response()
        # response.set_cookie('refresh', self.refresh_token)
        return response