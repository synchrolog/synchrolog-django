from setuptools import setup

setup(
    name='synchrolog-django',
    version='0.0.1',
    packages=['synchrolog_django'],
    url='',
    license='',
    author='',
    author_email='',
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
