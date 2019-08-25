import logging
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
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
