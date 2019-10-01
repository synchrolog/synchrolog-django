from setuptools import setup

setup(
    name='synchrolog-django',
    version='0.0.1',
    packages=['synchrolog_django'],
    url='https://github.com/synchrolog/synchrolog-django',
    license='Apache-2.0',
    author='Synchrolog',
    author_email='hello@synchrolog.com',
    description='Django middleware that sends request logs to Synchrolog',
    install_requires=[
        'certifi',
        'chardet',
        'Django',
        'idna',
        'pytz',
        'requests',
        'sqlparse',
        'urllib3',
    ],
)
