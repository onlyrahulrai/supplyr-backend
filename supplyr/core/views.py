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

from .serializers import UserDetailsSerializer, SellerProfilingSerializer, SellerProfilingDocumentsSerializer, CategoriesSerializer
from .permissions import IsUnapproved
from .models import SellerProfile, Category

from supplyr.utils.api.mixins import APISourceMixin

User = get_user_model()
  

class UserInfoMixin():

    # @staticmethod
    def get_user_info(self, user):
        extra_context = {}
        if hasattr(self, 'request'):
            extra_context['request'] = self.request

        serializer = UserDetailsSerializer(user, context=extra_context)
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


class CustomLoginView(LoginView, APISourceMixin):
    def get_response(self):
        response = super().get_response()
        print("SRC ", self.request.user)
        # response.data['user_info'] = response.data['user']
        # del response.data['user']
        # response.set_cookie('refresh', self.refresh_token)
        return response


class ProfilingView(APIView, UserInfoMixin):
    permission_classes = [IsUnapproved]

    def post(self, request, *args, **kwargs):
        # if(request.user.is_approved):
        #     return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['owner'] = request.user.pk
        
        existing_profile = SellerProfile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = SellerProfilingSerializer(existing_profile, data = data)
        else:
            serializer = SellerProfilingSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            serializer_data = self.inject_user_info(serializer.data, request.user)
            return Response(serializer_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilingDocumentsUploadView(APIView):    #Seller
    
    permission_classes = [IsUnapproved]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        
        data = request.data.copy()
        data['owner'] = request.user.pk

        existing_profile = SellerProfile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = SellerProfilingDocumentsSerializer(existing_profile, data = data)
        else:
            serializer = SellerProfilingDocumentsSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesView(APIView, UserInfoMixin):

    permission_classes = [IsUnapproved]

    def post(self, request, *args, **kwargs):

        sub_categories = request.data['sub_categories']
        profile = request.user.seller_profiles.first()
        profile.operational_fields.set(sub_categories)
        response = self.inject_user_info({'success': True}, request.user)

        return Response(response)