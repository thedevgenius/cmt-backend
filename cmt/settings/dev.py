from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://10.74.154.149:3000",
    "http://192.168.0.82:3000",
    "http://10.142.128.149:3000"
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://10.74.154.149:3000",
    "http://192.168.0.82:3000",
    "http://10.142.128.149:3000"
]