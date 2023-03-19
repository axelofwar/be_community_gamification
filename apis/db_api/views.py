import os
import sys
import json
import urllib.parse
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from .serializers import TweetSerializer
from .models import Tweet
from rest_framework.views import APIView, Response, status
from django.shortcuts import render, get_object_or_404
from api_utils import update_rules as ur
from api_utils import remove_rules as rr
from api_utils import stream_tools as st
import traceback

# get params from stream tools file and use memnbers/update_flag accordingly

# Create your views here.

# Default view for the API
params = st.params


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
        config = params.get_config()
        # Get the new value from the request data
        try:
            data = json.load(request.body)
            rule, tag = data.split(',')
            print("rule: ", rule)
            print("tag: ", tag)
        except Exception as err:
            print(
                f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
            if 'b' in str(request.body):
                # string = str(request.body)
                string = str(urllib.parse.unquote_plus(
                    request.body.decode("utf-8")))

                try:
                    # json_data = json.loads(string.split("=", 1))
                    json_data = json.load(string)
                except Exception as err:
                    print(
                        f"Error: {err} with request: {request} of data {string} and body: {request.body}")
                    return Response({'message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    data = json_data.replace("b'", "")
                    print("\ndata: ", data)
                    rule, tag = data.split(',')
                    print(f"\nrule: {rule}, tag: {tag}")
                    # rule = rule.replace("'", "")
                    tag = tag.replace("'", "")
                    tag = tag.replace(" ", "")
                    print(f"\nCleaned tag: {tag} ")
                except Exception as err:
                    # print("No b in request body")
                    return Response({f'No b in request string {json_data} of body {data} message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)
                    # print(
                    #     f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
                    # return Response({'message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    string = request.body.decode("utf-8")
                    json_data = json.loads(string.split("=", 1)[1])
                    print("\data: ", string)
                    data = string.replace("'", "")
                    # print("\ndata: ", data)
                    rule, tag = data.split(',')
                    print("\nrule: ", rule)
                    print("\ntag: ", tag)
                    # rule = rule.replace("'", "")
                    print("\nrule: ", rule)
                    tag = tag.replace("'", "")
                    tag = tag.replace(" ", "")
                    print("\ntag: ", tag)
                except Exception as err:
                    print(
                        f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
                    return Response({'message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    config.add_rule = rule
                    config.add_tag = tag

                # call function to update the rules
                    ur.main()
                    config.add_rule = ""
                    config.add_tag = ""
                    # Return a success response with the updated YAML file
                    return Response({'message': 'Config updated successfully', 'config_data': config}, status=status.HTTP_200_OK)
                except Exception as e:
                    # Return an error response if there was an exception while updating the YAML file
                    tb = traceback.format_exc()
                    err_msg = f"Error updating config: {str(e)}\n{tb}, rule: {config.add_rule}, tag: {config.add_tag}"
                    # Return an error response with the detailed error message
                    return Response({'message': err_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveRule(APIView):
    def post(self, request):
        config = params.get_config()
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
            config.remove_rule = data

            # call function from utils to remove rule
            rr.main()
            # Return a success response with the updated YAML file
            return Response({'message': 'Config updated successfully', 'config_data': config}, status=status.HTTP_200_OK)

        except Exception as e:
            # Return an error response if there was an exception while updating the YAML file
            return Response({'message': 'Error updating config: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
