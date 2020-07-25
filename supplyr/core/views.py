from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import mixins, generics
from rest_framework.parsers import MultiPartParser, FormParser

from dj_rest_auth.views import LoginView

from .serializers import UserDetailsSerializer, ProfilingSerializer, ProfilingDocumentsSerializer, CategoriesSerializer
from .models import Profile, Category

User = get_user_model()
  

class UserInfoMixin():

    @staticmethod
    def get_user_info(user):
        serializer = UserDetailsSerializer(user)
        return serializer.data

    def inject_user_info(self, data, user):
        user_info = self.get_user_info(user)
        _data = data # so that it may work if someone passes serializer.data, to which changes do not reflect wothout making a copy
        _data['user_info'] = user_info
        return _data

        


class UserDetailsView(APIView, UserInfoMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        response_data = self.inject_user_info({}, user)

        return Response(response_data)


class CustomLoginView(LoginView):
    def get_response(self):
        response = super().get_response()

        # response.data['user_info'] = response.data['user']
        # del response.data['user']
        # response.set_cookie('refresh', self.refresh_token)
        return response


class ProfilingView(APIView, UserInfoMixin):
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     #TODO add approved validation
    #     existing_profile = Profile.objects.filter(owner=request.user).first()
    #     if not existing_profile:
    #         return Response("No data for user", status=status.HTTP_404_NOT_FOUND)
    #     serializer = ProfilingSerializer(existing_profile)
    #     return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if(request.user.status == 'approved'):
            return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)
        

        data = request.data.copy()
        data['owner'] = request.user.pk
        
        existing_profile = Profile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = ProfilingSerializer(existing_profile, data = data)
        else:
            serializer = ProfilingSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            serializer_data = self.inject_user_info(serializer.data, request.user)
            return Response(serializer_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilingDocumentsUploadView(APIView):
    
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        if(request.user.status == 'approved'):
            return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['owner'] = request.user.pk

        existing_profile = Profile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = ProfilingDocumentsSerializer(existing_profile, data = data)
        else:
            serializer = ProfilingDocumentsSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesView(APIView):

    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):

    #     categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
    #     serializer = CategoriesSerializer(categories, many=True)
    #     serializer_data = serializer.data

    #     user_selected_sub_categories = request.user.profiles.first().operational_fields.all().values_list('id', flat=True)
        
    #     response_data = {
    #         'categories': serializer_data,
    #         'selected_sub_categories': user_selected_sub_categories
    #     }
    #     return Response(response_data)

    def post(self, request, *args, **kwargs):

        if(request.user.status == 'approved'):
            return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)

        sub_categories = request.data['sub_categories']
        profile = request.user.profiles.first()
        profile.operational_fields.set(sub_categories)
        return Response(True)