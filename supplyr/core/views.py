from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from dj_rest_auth.views import LoginView

from .serializers import UserDetailsSerializer, ProfilingSerializer
from .models import Entity

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


class ProfilingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if(request.user.status == 'approved'):
            return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)
        

        data = request.data.copy()
        data['owner'] = request.user.pk
        
        existing_profile = Entity.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = ProfilingSerializer(existing_profile, data = data)
        else:
            serializer = ProfilingSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)