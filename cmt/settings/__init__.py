import os

ENV = os.getenv("ENVIRONMENT", "dev")

if ENV == "production":
    from .production import *
elif ENV == "staging":
    from .staging import *
else:
    from .dev import *