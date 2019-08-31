# Synchrolog

## Installation
`pip install git+https://github.com/synchrolog/synchrolog-django.git@master`

## Usage

Add access token to your application config (`/yourproject/settings.py`)

Add synchrolog middleware (`/yourproject/settings.py`)
```python
MIDDLEWARE = [
    # It MUST be the first middleware
    'synchrolog_django.middleware.SynchrologMiddleware',
    ...
]

SYNCHROLOG_API_KEY = os.getenv('SYNCHROLOG_API_KEY')

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
        }
    }

```

## Logger handlers
 - synchrolog_django.RequestHandler - handler that sends messages to Synchrolog server and wait when message will be delivered.
 - synchrolog_django.QueueHandler - handler that use queue and Request handler for sending logs in asynchronous way (without blocking request).

## Note
Such as Django doesn't raises errors, it's not possible to retrieve stacktrace of all 4xx errors, 
but library catch unhandled exception and their stacktrace. 