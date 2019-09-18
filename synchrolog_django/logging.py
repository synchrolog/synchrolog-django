import logging
import traceback
from datetime import datetime
from logging.handlers import QueueListener
from queue import Queue
from uuid import uuid4

import requests
from django.conf import settings

from .threadlocal import local

ANONYMOUS_KEY = 'synchrolog_anonymous_id'
USER_KEY = 'synchrolog_user_id'
RAW_ANONYMOUS_KEY = 'synchrolog_anonymous_id_raw'


queue = Queue()


def setup_logging():
    logging.setLogRecordFactory(_build_make_record_function())


def _build_make_record_function():
    """ Create record factory based on previous factory
    and synchrolog factory for appending synchrolog data
    """
    prev_factory = logging.getLogRecordFactory()

    def make_record(*arguments, **kwargs):
        record = prev_factory(*arguments, **kwargs)
        return _synchrolog_record_factory(record)

    return make_record


def get_last_frame(tb):
    """ Get frame that must be showed to user. In some case it's not the
    last stack frame, ex: abort(404)
     """
    frames = traceback.extract_tb(tb)
    if not frames:
        return None

    target_frame = frames[-1]
    for frame in frames[::-1]:
        # ignore stack from installed and std packages
        if 'site-packages' in frame.filename or '/synchrolog_flask' in frame.filename:
            continue
        target_frame = frame
        break
    return target_frame


def _generate_uuid():
    return str(uuid4())


class RequestHandler(logging.Handler):

    def __init__(self):
        access_token = getattr(settings, 'SYNCHROLOG_API_KEY', None)
        assert bool(access_token), 'Provide SYNCHROLOG_ACCESS_TOKEN variable in your settings.py'
        self.access_token = access_token
        super().__init__()

    def emit(self, record):
        """ Actually send synchrolog data to remote server """
        data = getattr(record, 'synchrolog', {})
        if not data:
            return

        url = data.pop('url', None)

        if not url:
            return

        headers = {'Authorization': f'Basic {self.access_token}'}
        response = requests.post(url=url, json=data, headers=headers)
        if response.status_code >= 400:
            print('Could not send logging info to synchrolog server\n\n', response.text)


class QueueHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        self._handler = RequestHandler()

        self._queue_handler = logging.handlers.QueueHandler(queue)
        self._queue_handler.setLevel(level)

        self._listener = QueueListener(queue, self._handler)
        self._listener.start()
        super().__init__(level)

    def emit(self, record):
        self._queue_handler.emit(record)


def _synchrolog_record_factory(record):
    request = getattr(local, 'synchrolog_request', None)
    if not request:
        return record

    anonymous_id = request.COOKIES.get(ANONYMOUS_KEY, _generate_uuid())
    request.COOKIES[RAW_ANONYMOUS_KEY] = anonymous_id
    user_id = request.COOKIES.get(USER_KEY, '')

    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    synchrolog = {
        'timestamp': timestamp,
        'anonymous_id': anonymous_id,
        'user_id': user_id,
        'source': 'backend',
    }

    # For logs with level above ERROR and logs without exception info,
    # send backend log.
    if record.levelno < logging.ERROR or not record.exc_info:
        synchrolog = {
            **synchrolog,
            'event_type': 'log',
            'url': 'https://input.synchrolog.com/v1/track-backend',
            'log': {
                'timestamp': timestamp,
                'message': record.getMessage()
            }
        }
    else:
        # For logs with exception send request related info
        _, exception, tb = record.exc_info
        frame = get_last_frame(tb)

        ip_address = (
                request.headers.get('x-forwarded-for')
                or request.headers.get('http_x-forwarded-for')
                or request.META.get('REMOTE_ADDR')
                or ''
        )

        filename = frame.filename if frame else ''

        # read source code of file
        source_code = ''
        if filename:
            with open(filename) as file:
                source_code = file.read()

        backtrace = ''.join(traceback.format_tb(tb))
        synchrolog = {
            **synchrolog,
            'event_type': 'error',
            'url': 'https://input.synchrolog.com/v1/track-backend-error',
            'error': {
                'status': str(getattr(exception, 'code', 500)),
                'description': record.getMessage(),
                'backtrace': backtrace,
                'ip_address': ip_address,
                'user_agent': request.headers.get('user-agent'),
                'file_name': filename,
                'line_number': frame.lineno if frame else '',
                'file': source_code,
            }
        }
        if getattr(exception, 'code', None):
            record.exc_info = None

    record.synchrolog = synchrolog
    return record


def log_response(response, request, logger):
    if getattr(response, '_has_been_logged', False):
        return

    if response.status_code >= 500:
        level = 'error'
    elif response.status_code >= 400:
        level = 'warning'
    else:
        level = 'info'

    getattr(logger, level)(
        '%s: %s', response.reason_phrase, request.path,
        extra={
            'status_code': response.status_code,
            'request': request,
        },
    )
    response._has_been_logged = True
