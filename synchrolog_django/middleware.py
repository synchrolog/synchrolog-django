import logging
from datetime import datetime

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .logging import setup_logging, RAW_ANONYMOUS_KEY, ANONYMOUS_KEY, log_response
from .threadlocal import local


logger = logging.getLogger('synchrolog.middleware')


class SynchrologMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        setup_logging()

    def process_request(self, request):
        if 'synchrolog-time' in request.path:
            return JsonResponse({'time': datetime.now().isoformat()})

        local.synchrolog_request = request

    def process_response(self, request, response):

        log_response(
            response=response,
            request=request,
            logger=logger,
        )
        anonymous_id_raw = request.COOKIES.get(RAW_ANONYMOUS_KEY)
        anonymous_id = request.COOKIES.get(ANONYMOUS_KEY)
        if anonymous_id_raw != anonymous_id:
            response.set_cookie(ANONYMOUS_KEY, anonymous_id_raw)

        try:
            del local.synchrolog_request
        except AttributeError:
            pass
        return response
