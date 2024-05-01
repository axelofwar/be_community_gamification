import json
# import urllib.parse
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
import logging

# get params from stream tools file and use memnbers/update_flag accordingly
params = st.params


class Index(APIView):
    """
    View to confirm API operation separate from database connection
    """
    # throttle_classes = [throttle.CustomThrottle(100, 60)]
    # throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request, format=None):
        """
        Get function for returning the engagement table data serialized

        :param request: the request from the get call with its data in body
        :return: Response from get call
        """
        content = {
            'status': 'request was permitted'
        }
        return Response(content)


# View for the PFP_Table
class pfpTable(APIView):
    """
    View to return database captured data from pfp table in tweet model. Use cache where appropraite.
    """
    # throttle_classes = [throttle.CustomThrottle]

    def get(self, request, format=None):
        """
        Get function for returning the engagement table data serialized

        :param request: the request from the get call with its data in body
        :return: Response from get call
        """
        cache_key = 'pfpTable_data'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        else:
            queryset = Tweet.objects.all().order_by('-Impressions')
            serializer = TweetSerializer(queryset, many=True)
            cache.set(cache_key, serializer.data, 60)
            return Response(serializer.data, status=status.HTTP_200_OK)


class engagementTable(APIView):
    """
    View to return database captured data from engagement table in tweet model. Use cache where appropraite.
    """
    # TODO: throttle_classes = [throttle.CustomThrottle]

    def get(self, request, format=None):
        """
        Get function for returning the engagement table data serialized

        :param request: the request from the get call with its data in body
        :return: Response from get call
        """
        cache_key = 'engagementTable_data'
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
    """
    View to return database captured data from admin table in tweet model. Use cache where appropraite.
    
    Depreciated Global Reach ranking system due to nft inspect api issues
    """
    # TODO: throttle_classes = [throttle.CustomThrottle]
    def get(self, request, format=None):
        """
        Get function for admin table

        :param request: the request from the get call
        :return: Response from get call
        """
        # queryset = Tweet.objects.all().order_by('-Global_Reach')
        queryset = Tweet.objects.all().order_by('-Impressions')
        serializer = TweetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        Post function for admin table

        :param request: the request from the post call
        :return: Response from post call
        """
        serializer = TweetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        """
        Put function for admin table

        :param request: the request from the put call
        :param pk: priamry key for put call
        :return: Response from put call
        """
        tweet = get_object_or_404(Tweet, pk=pk)
        serializer = TweetSerializer(tweet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete function for admin table

        :param request: the request from the delete call
        :param pk: primary key for delete call
        :return: Response from delete call
        """
        tweet = get_object_or_404(Tweet, pk=pk)
        tweet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# TODO: fix this to properly parse the request body and update the rules
# ultimately I think I may remove this in favor of ssh into the server and update project's tracked in filtered stream directly
# OR I could just update the collections called and deploy a new version of the app, with replica handling in the paid version of render

class UpdateRule(APIView):
    """
    Update the rules on the twitter stream via API

    TODO: fix this to properly parse the request body and update the rules - currently easier to just ssh in and shell call update scripts
    """
    def post(self, request):
        """
        Post function to post new rules to the UpdateRule module

        :param request: the request from the post call
        :param return: Response from post call
        """
        config = params.get_config()
        # Get the new value from the request data
        try:
            data = json.loads(request.body)
            rule, tag = data.split(',')
            logging.info(f"rule: {rule} - tag: {tag}")
        except Exception as err:
            logging.error(
                f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
            if 'b' in str(request.body):
                string = str(request.body.decode("utf-8"))
                # string = str(urllib.parse.unquote_plus(
                #     request.body.decode("utf-8")))

                try:
                    json_data = json.loads(string.split("=", 1))
                except Exception as err:
                    logging.error(
                        f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
                    return Response({'message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    data = json_data.replace("b'", "")
                    rule, tag = data.split(',')
                    # rule = rule.replace("'", "")
                    tag = tag.replace("'", "")
                    tag = tag.replace(" ", "")
                    logging.info(f"\ndata: {data} - rule: {rule} - tag: {tag}")
                except Exception as err:
                    logging.error(
                        f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
                    return Response({f'No b in request string {json_data} of body {data} message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    string = request.body.decode("utf-8")
                    json_data = json.loads(string.split("=", 1)[1])
                    logging.info(f"\ndata: {string}")
                    data = string.replace("'", "")
                    rule, tag = data.split(',')
                    tag = tag.replace("'", "")
                    tag = tag.replace(" ", "")
                    logging.info(f"\nrule: {rule} - tag: {tag}")
                except Exception as err:
                    logging.error(
                        f"Error: {err} with request: {request} of type {type(request)} and data: {request.body}")
                    return Response({'message': 'Error: ' + str(err)}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    logging.info(f"RULE: {request.POST.get('rule')}")
                    logging.info(f"TAG: {request.POST.get('tag')}")
                    rule = request.POST.get('rule')
                    tag = request.POST.get('tag')
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
    """
    Class for removing rules from the twitter stream via API
    """
    def post(self, request) -> Response:
        """
        Post call to remove rules from the stream API

        :param request: the post request with its data
        :return: Response from post call
        """
        config = params.get_config()
        # Get the new value from the request data
        try:
            data = json.loads(request.body)
        except Exception as err:
            logging.error(
                f"Error: {err} with request: {request} of data: {request.body}")
            if 'b' in str(request.body):
                string = str(request.body)
                data = string.replace("b'", "")
            data = json.dumps(data)
        try:
            config.remove_rule = request.POST.get('rule')

            # call function from utils to remove rule
            rr.main()
            # Return a success response with the updated YAML file
            return Response({'message': 'Config updated successfully', 'config_data': config}, status=status.HTTP_200_OK)

        except Exception as e:
            # Return an error response if there was an exception while updating the YAML file
            return Response({'message': 'Error updating config: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
