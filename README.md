# Synchrolog

## Installation
`pip install synchrolog-django`

## Usage

Add access token to your application config (`/yourproject/settings.py`)

Add synchrolog middleware (`/yourproject/settings.py`)
```python
MIDDLEWARE = [
    # It MUST be the first middleware
    'synchrolog_django.middleware.SynchrologMiddleware',
    ...
]

SYNCHROLOG_ACCESS_TOKEN = os.getenv('SYNCHROLOG_API_KEY')

# Configure logging
LOGGING = {
    'handlers': {
        # add synchrolog logger handler
        'synchrolog': {
            'class': 'synchrolog_django.QueueHandler',
        },
    },
    'loggers': {
        # Add synchrolog handler to root or your own logger
        '': {
            'handlers': ['synchrolog'],
        },
        # Change default behaviour of django loggers, because their call made out side of middlewares that 
        # we can not control. 
        'django.server': {'level': 'CRITICAL'},
        'django.request': {'level': 'CRITICAL'},
    }

```

## Logger handlers
 - synchrolog_django.RequestHandler - handler that sends messages to Synchrolog server and waits when the message will be delivered.
 - synchrolog_django.QueueHandler - handler that uses queue and RequestHandler for sending logs in an asynchronous way (without blocking request).

## Note
Such as Django doesn't raise errors, it's not possible to retrieve stacktrace of all 4xx errors, but library still catches the unhandled exception and their stacktrace.


## For running tests
```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python -m unittest tests/test_handler.py tests/test_logging.py 
```
