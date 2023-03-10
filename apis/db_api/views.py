from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.shortcuts import get_object_or_404

# Create your views here.


# Default view for the API
class Index(APIView):
    # throttle_classes = [throttle.CustomThrottle(100, 60)]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)


class Favicon(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)


# View for the PFP_Table
class pfpTable(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request, format=None):
        cache_key = 'pfpTable_data'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        else:
            queryset = Tweet.objects.all().order_by('-Impressions')
            serializer = TweetSerializer(queryset, many=True)
            cache.set(cache_key, serializer.data, 60)
            return Response(serializer.data, status=status.HTTP_200_OK)


# Admin view for the PFP_Table
class adminPfpTable(APIView):
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request, format=None):
        queryset = Tweet.objects.all().order_by('-Impressions')
        serializer = TweetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = TweetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        tweet = get_object_or_404(Tweet, pk=pk)
        serializer = TweetSerializer(tweet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        tweet = get_object_or_404(Tweet, pk=pk)
        tweet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
