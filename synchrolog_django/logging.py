import logging
import traceback
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from uuid import uuid4

import requests

from . import local

ANONYMOUS_KEY = 'synchrolog_anonymous_id'
USER_KEY = 'synchrolog_user_id'

queue = Queue()


def setup_logging(level, access_token, use_queue):
    handler = _RequestHandler(access_token)
    handler.setLevel(level)

    # we can add handlers to root handler, and it will be work, because by default Logger
    # class contains variable `propagate` equal to True that will propagate record
    # to parent logger handlers
    logger = logging.root
    logger.level = level
    if use_queue:
        queue_handler = QueueHandler(queue)
        queue_handler.setLevel(level)
        logger.addHandler(queue_handler)
        listener = QueueListener(queue, handler)
        listener.start()
    else:
        logger.addHandler(handler)

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


class _RequestHandler(logging.Handler):

    def __init__(self, access_token):
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


def _synchrolog_record_factory(record):
    request = getattr(local, 'synchrolog_request', None)
    if not request:
        return record

    anonymous_id = request.COOKIES.get(ANONYMOUS_KEY, _generate_uuid())
    user_id = request.COOKIES.get(USER_KEY)

    timestamp = datetime.now().isoformat()
    synchrolog = {
        'event_type': 'log',
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

