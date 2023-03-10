# Create custom throttling classes for the admin site
# This is to prevent the admin site from being used to perform DDoS attacks
# The default throttling class is the AnonRateThrottle class, which limits the number of requests per minute
# We can create our own throttling classes by inheriting from the AnonRateThrottle class
# We can then set the rate and scope attributes to configure the throttling class
# The rate attribute is the number of requests per minute
# The scope attribute is the scope of the throttling class, which can be either 'user' or 'anon'
# The scope attribute determines whether the throttling class is applied to authenticated users or anonymous users
# The default scope is 'anon', which means that the throttling class is applied to anonymous users
# The scope can be set to 'user', which means that the throttling class is applied to authenticated users
# The scope can also be set to None, which means that the throttling class is applied to both authenticated and anonymous users

from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import caches


class BasicThrottle(SimpleRateThrottle):
    ALLOWED_REQUESTS = 100
    TIME_INTERVAL = 60
    scope = 'custom'

    # throttle by IP address
    def get_ident(self, request):
        return request.META.get('REMOTE_ADDR', None)

    # throttle by IP address and user
    def get_cache_key(self, request, view):
        return self.get_ident(request)

    def allow_request(self, request, view):
        if self.get_cache_key(request, view):
            if self.cache.get(self.get_cache_key(request, view)):
                return False
            self.cache.set(self.get_cache_key(request, view), True, self.rate)
        return True


class CustomThrottle(SimpleRateThrottle):
    scope = 'custom'

    def __init__(self, get_response=None, num_requests=100, time_interval=60):
        super().__init__(get_response)
        self.num_requests = num_requests
        self.time_interval = time_interval
        self.cache = caches('default')

    def get_ident(self, request):
        """
        Returns the IP address of the client making the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_cache_key(self, request, view):
        """
        Returns the cache key for the current request. By default, this is the
        client's IP address.
        """
        return self.get_ident(request)

    def allow_request(self, request, view):
        """
        Determines whether the request should be allowed based on the request rate
        of the client making the request.
        """
        # Get the cache key for the current request
        cache_key = self.get_cache_key(request, view)

        # If the cache key is not set, allow the request
        if not cache_key:
            return True

        # Get the cache entry for the current client
        cache_entry = self.cache.get(cache_key)

        # If the cache entry exists and the number of requests exceeds the
        # allowed number of requests per time interval, disallow the request
        if cache_entry and cache_entry['requests'] >= self.num_requests:
            return False

        # If the cache entry does not exist, create a new cache entry for the
        # current client and allow the request
        if not cache_entry:
            cache_entry = {'requests': 1}
            self.cache.set(cache_key, cache_entry, self.time_interval)
            return True

        # If the cache entry exists and the number of requests is less than
        # the allowed number of requests per time interval, increment the
        # number of requests and allow the request
        if cache_entry['requests'] < self.num_requests:
            cache_entry['requests'] += 1
            self.cache.set(cache_key, cache_entry, self.time_interval)
            return True

        # Otherwise, disallow the request
        return False
