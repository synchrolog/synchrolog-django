from datetime import datetime

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .logging import setup_logging
from .threadlocal import local


class SynchrologMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        setup_logging()

    def process_request(self, request):
        if 'synchrolog-time' in request.path:
            return JsonResponse({'time': datetime.now().isoformat()})

        local.synchrolog_request = request

    def process_response(self, request, response):
        try:
            del local.synchrolog_request
        except AttributeError:
            pass
        return response
