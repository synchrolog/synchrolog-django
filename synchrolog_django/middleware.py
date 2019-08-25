import logging
from datetime import datetime

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from . import local
from .logging import setup_logging


class SynchrologMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)

        access_token = getattr(settings, 'SYNCHROLOG_ACCESS_TOKEN', None)
        assert bool(access_token), 'Provide SYNCHROLOG_ACCESS_TOKEN variable in your settings.py'

        use_queue = getattr(settings, 'SYNCHROLOG_USE_QUEUE', True)

        logger_level = getattr(settings, 'SYNCHROLOG_LOGGING_LEVEL', logging.root.level)
        setup_logging(
            level=logger_level,
            use_queue=use_queue,
            access_token=access_token,
        )

    def process_request(self, request):
        print(request.path)
        if 'synchrolog-time' in request.path:
            return JsonResponse({'time': datetime.now().isoformat()})

        local.synchrolog_request = request

    def process_response(self, request, response):
        try:
            del local.synchrolog_request
        except AttributeError:
            pass
        return response


"""

The developer must be able to deliver a python package, or two packages, that integrate Django and Flask apps to 
Synchrolog. It must include installation instructions and functional tests. We already have this library for NodeJS 
and Ruby on Rails. For more details please refer to our libraries here https://github.com/synchrolog. 

The idea here is that for every log entry written in the log file and every exception raised in the web app, 
we need to send a copy of that in our servers. All information sent to our servers must be identified with an API key 
and an anonymous_id or user_id. 

What does the package/middleware do?


Have a route 'GET /synchrolog-time' that returns server time in ISO-8601 format. https://synchrolog.com/docs#get-time 
Copy everything that gets written in the log file and send it to Synchrolog in the following format 
https://synchrolog.com/docs#track-log Capture all exceptions (similar behavior of Sentry, also note that we should 
not handle the exception), and send a copy of the error to Synchrolog in the following format 
https://synchrolog.com/docs#track-error 

This middleware must be the first one to be loaded in the Django/Flask apps. Logs and errors being tracked must 
include an API key, and anonymous_id or user_id. The API key must be set on the app configuration. The anonymous_id 
and user_id identifiers are available through the request cookies (synchrolog_anonymous_id, synchrolog_user_id). If 
none of them are set, then set a value to the synchrolog_anonymous_id cookie to make it available for the next 
requests. The value of synchrolog_anonymous_id must a random value, preferably UUID v4. 

You can send API requests directly to https://input.synchrolog.com using this API key: ss53et50z2jn24ltn6yk7xypfsc7pcp8

In advance, I created 3 GitHub repos where the code must reside. Feel free to use the ones that better fit your 
solution. Please provide your GitHub username or email so I can add you as a collaborator. The repositories are: 


https://github.com/synchrolog/synchrolog-flask
https://github.com/synchrolog/synchrolog-django
https://github.com/synchrolog/synchrolog-python

You can user our Ruby on Rails library as an example, but I don't know what's the best way to translate that to 
Django or Flask. https://github.com/synchrolog/synchrolog-ruby/blob/master/lib/synchrolog/middleware.rb """
