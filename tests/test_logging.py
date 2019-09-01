import copy
import logging
import logging.config
import unittest
from http.cookies import SimpleCookie
from unittest import mock

from django.conf import settings
from django.test import override_settings, RequestFactory

from synchrolog_django import SynchrologMiddleware

try:
    settings.configure()
except RuntimeError:
    pass

logger = logging.getLogger('test')
logger.setLevel(logging.DEBUG)


class Object:
    ...


LOGGING = {
    'version': 1,
    'handlers': {
        'synchrolog': {
            'class': 'synchrolog_django.RequestHandler',
        },
    },
    'loggers': {
        'test': {
            'handlers': ['synchrolog'],
            'propagate': True,
        }
    }
}


def settings_decorator(func):
    return mock.patch(
        'requests.post',
        side_effect=mocked_request_post
    )(override_settings(
        SYNCHROLOG_API_KEY='123',
        LOGGING=LOGGING
    )(func))


def mocked_request_post(*args, **kwargs):
    obj = Object()
    obj.status_code = 200
    return obj


def mocked_extract_tb(tb, limit=None):
    obj = Object()
    obj.filename = __file__
    obj.lineno = '1'
    return [obj]


def mocked_format_tb(tb):
    return 'TRACEBACK'


class MiddlewareMiddleware(unittest.TestCase):

    @settings_decorator
    def setUp(self, post_mock) -> None:
        self.middleware = SynchrologMiddleware()
        self.factory = RequestFactory()
        self.factory.cookies = SimpleCookie({
            'synchrolog_user_id': '1',
            'synchrolog_anonymous_id': '2'
        })
        logging.config.dictConfig(LOGGING)

    @settings_decorator
    def test_get_time(self, post_mock) -> None:
        response = self.middleware.process_request(self.factory.get('/synchrolog-time'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'time' in response.content)

    @settings_decorator
    def test_logging_without_user_id(self, post_mock) -> None:
        def view(*args, **kwargs):
            logger.info('SOME MSG')

        self.middleware.get_response = view
        factory = copy.deepcopy(self.factory)
        factory.cookies = {}
        request = factory.get('/')
        self.middleware(request)

        post_mock.assert_called()
        post_mock.assert_called_with(
            headers={'Authorization': 'Basic 123'},
            json={
                'event_type': 'log', 'timestamp': mock.ANY,
                'anonymous_id': mock.ANY, 'user_id': None,
                'source': 'backend',
                'log': {'timestamp': mock.ANY, 'message': 'SOME MSG'},
            },
            url='https://input.synchrolog.com/v1/track-backend',
        )
        self.assertIsNotNone(post_mock.call_args[1]['json']['anonymous_id'])

    @settings_decorator
    def test_logging_with_user_id(self, post_mock) -> None:
        def view(*args, **kwargs):
            logger.info('SOME MSG')

        self.middleware.get_response = view

        request = self.factory.get('/')
        self.middleware(request)

        post_mock.assert_called()
        post_mock.assert_called_with(
            headers={'Authorization': 'Basic 123'},
            json={
                'event_type': 'log', 'timestamp': mock.ANY,
                'anonymous_id': '2', 'user_id': '1',
                'source': 'backend',
                'log': {'timestamp': mock.ANY, 'message': 'SOME MSG'},
            },
            url='https://input.synchrolog.com/v1/track-backend',
        )
        self.assertIsNotNone(post_mock.call_args[1]['json']['anonymous_id'])

    @settings_decorator
    def test_logging_error_without_traceback(self, post_mock) -> None:
        def view(*args, **kwargs):
            logger.error('SOME MSG')

        self.middleware.get_response = view

        request = self.factory.get('/')
        self.middleware(request)

        post_mock.assert_called()
        post_mock.assert_called_with(
            headers={'Authorization': 'Basic 123'},
            json={
                'event_type': 'log', 'timestamp': mock.ANY,
                'anonymous_id': '2', 'user_id': '1',
                'source': 'backend',
                'log': {'timestamp': mock.ANY, 'message': 'SOME MSG'},
            },
            url='https://input.synchrolog.com/v1/track-backend',
        )
        self.assertIsNotNone(post_mock.call_args[1]['json']['anonymous_id'])

    @mock.patch('traceback.format_tb', side_effect=mocked_format_tb)
    @mock.patch('traceback.extract_tb', side_effect=mocked_extract_tb)
    @settings_decorator
    def test_logging_error_with_traceback(self, post_mock, tb_mock, format_tb_mock) -> None:
        def view(*args, **kwargs):
            logger.error('SOME MSG', exc_info=True)

        self.middleware.get_response = view

        request = self.factory.get('/')
        self.middleware(request)

        post_mock.assert_called()
        post_mock.assert_called_with(
            headers={'Authorization': 'Basic 123'},
            json={
                'event_type': 'log',
                'timestamp': mock.ANY,
                'anonymous_id': '2', 'user_id': '1',
                'source': 'backend',
                'error': {
                    'status': '500', 'description': 'SOME MSG', 'backtrace': 'TRACEBACK', 'ip_address': '127.0.0.1',
                    'user_agent': None, 'file_name': __file__, 'line_number': '1', 'file': mock.ANY
                },
            },
            url='https://input.synchrolog.com/v1/track-backend-error',
        ),

        self.assertIsNotNone(post_mock.call_args[1]['json']['anonymous_id'])
