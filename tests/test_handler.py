import unittest
from unittest import mock

from django.conf import settings
from django.test import override_settings

from synchrolog_django import RequestHandler

try:
    settings.configure()
except RuntimeError:
    pass


class Object:
    ...


settings_decorator = override_settings(SYNCHROLOG_API_KEY='123')


class RequestHandlerInit(unittest.TestCase):

    @override_settings(SYNCHROLOG_API_KEY='123')
    def test_success_init(self):
        handler = RequestHandler()
        self.assertEqual(handler.access_token, '123')

    @override_settings()
    def test_failed_init(self):
        with self.assertRaises(AssertionError):
            RequestHandler()


def mocked_request_post(*args, **kwargs):
    obj = Object()
    obj.status_code = 200
    return obj


class RequestHandlerEmit(unittest.TestCase):

    @mock.patch('requests.post', side_effect=mocked_request_post)
    @settings_decorator
    def test_without_synchrolog_data(self, mock_post):
        handler = RequestHandler()
        obj = Object()
        handler.emit(obj)
        mock_post.assert_not_called()

    @mock.patch('requests.post', side_effect=mocked_request_post)
    @settings_decorator
    def test_without_url_in_data(self, mock_post):
        handler = RequestHandler()
        obj = Object()
        obj.synchrolog = {'msg': 'some msg'}
        handler.emit(obj)
        mock_post.assert_not_called()

    @mock.patch('requests.post', side_effect=mocked_request_post)
    @settings_decorator
    def test_ok(self, mock_post):
        handler = RequestHandler()
        obj = Object()
        obj.synchrolog = {'url': 'https://synchrolog.org', 'msg': 'SOME MSG'}
        handler.emit(obj)
        mock_post.assert_called()
