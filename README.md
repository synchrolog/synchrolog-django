# Synchrolog

## Installation
`pip install git+https://github.com/synchrolog/synchrolog-django.git@master`

## Usage

Add access token to your application config (`/yourproject/settings.py`)

```python
SYNCHROLOG_ACCESS_TOKEN = '123'
```

Add synchrolog middleware (`/yourproject/settings.py`)
```python
MIDDLEWARE = [
    'synchrolog_django.middleware.SynchrologMiddleware',
    ...
]
```

## Configuration
 * SYNCHROLOG_USE_QUEUE: bool (default true and recommended) - if value is true than all logs to Synchrolog 
 will send in another thread with queue without blocking current request.
 if values is false, than every logger calls will block current request and will wait outcoming 
 request tp Synchrolog
 * SYNCHROLOG_LOGGING_LEVEL: int (default logging.root.level) - level of all logs in system.

## Note
Such as Django doesn't raises errors, it's not possible to retrieve stacktrace of all 4xx errors, 
but library catch unhandled exception and their stacktrace. 