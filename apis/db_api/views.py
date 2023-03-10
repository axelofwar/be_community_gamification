from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from api import throttling as throttle

# Create your views here.


# Default view for the API
class Index(APIView):
    # throttle_classes = [throttle.CustomThrottle]
    # throttle_classes = [throttle.CustomThrottle(100, 60)]

    def get(self, request, *args, **kwargs):
        return HttpResponse("Hello, world!")


class Favicon(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request, *args, **kwargs):
        return HttpResponse(status=204)


# View for the PFP_Table
class pfpTable(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request):
        queryset = Tweet.objects.all().order_by('-Impressions')
        serializer = TweetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Admin view for the PFP_Table
class adminPfpTable(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request):
        queryset = Tweet.objects.all()
        serializer = TweetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TweetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
