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

class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserDetailsSerializer(user)
        serializer_data = serializer.data

        # if user.status != 'approved':
        #     profiling_data = {}

        #     ### Category Information
        #     categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
        #     serializer = CategoriesSerializer(categories, many=True)
        #     serializer_data = serializer.data

        #     user_selected_sub_categories = request.user.profiles.first().operational_fields.all().values_list('id', flat=True)
            
        #     response_data = {
        #         'categories': serializer_data,
        #         'selected_sub_categories': user_selected_sub_categories
        #     }
        #     profiling_data['categories'] = response_data


        return Response(serializer_data)


class CustomLoginView(LoginView):
    def get_response(self):
        response = super().get_response()
        # response.set_cookie('refresh', self.refresh_token)
        return response


class ProfilingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        #TODO add approved validation
        existing_profile = Profile.objects.filter(owner=request.user).first()
        if not existing_profile:
            return Response("No data for user", status=status.HTTP_404_NOT_FOUND)
        serializer = ProfilingSerializer(existing_profile)
        return Response(serializer.data)

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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

    def get(self, request, *args, **kwargs):

        categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
        serializer = CategoriesSerializer(categories, many=True)
        serializer_data = serializer.data

        user_selected_sub_categories = request.user.profiles.first().operational_fields.all().values_list('id', flat=True)
        
        response_data = {
            'categories': serializer_data,
            'selected_sub_categories': user_selected_sub_categories
        }
        return Response(response_data)