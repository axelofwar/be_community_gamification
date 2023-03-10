import os
import sys
import json
import yaml
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from .serializers import *
from .models import *
from rest_framework.views import APIView, Response, status
from django.shortcuts import render, get_object_or_404
from utils import update_rules as ur
from utils import remove_rules as rr


# Get the parent directory of the current file


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


class UpdateRule(APIView):
    def post(self, request):
        # Get the new value from the request data
        try:
            data = json.loads(request.body)
        except Exception as err:
            print(
                f"Error: {err} with request: {request} of data: {request.body}")
            if 'b' in str(request.body):
                string = str(request.body)
                data = string.replace("b'", "")
            data = json.dumps(data)
        try:
            # Read the YAML file and update the ADD_RULE keypair
            with open('../utils/yamls/config.yml', 'r') as yaml_file:
                config_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
                config_data['ADD_RULE'] = data

            # Save the updated YAML file
            with open('../utils/yamls/config.yml', 'w') as yaml_file:
                yaml.dump(config_data, yaml_file)

            # call function to update the rules
            ur.main()

            # Return a success response with the updated YAML file
            return Response({'message': 'Config updated successfully', 'config_data': config_data}, status=status.HTTP_200_OK)

        except Exception as e:
            # Return an error response if there was an exception while updating the YAML file
            return Response({'message': 'Error updating config: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveRule(APIView):
    def post(self, request):
        # Get the new value from the request data
        try:
            data = json.loads(request.body)
        except Exception as err:
            print(
                f"Error: {err} with request: {request} of data: {request.body}")
            if 'b' in str(request.body):
                string = str(request.body)
                data = string.replace("b'", "")
            data = json.dumps(data)
        try:
            # Read the YAML file and update the ADD_RULE keypair
            with open('../utils/yamls/config.yml', 'r') as yaml_file:
                config_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
                config_data['REMOVE_RULE'] = data

            # Save the updated YAML file
            with open('../utils/yamls/config.yml', 'w') as yaml_file:
                yaml.dump(config_data, yaml_file)

            # call function from utils to remove rule
            rr.main()
            # Return a success response with the updated YAML file
            return Response({'message': 'Config updated successfully', 'config_data': config_data}, status=status.HTTP_200_OK)

        except Exception as e:
            # Return an error response if there was an exception while updating the YAML file
            return Response({'message': 'Error updating config: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
