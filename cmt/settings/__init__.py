import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

ENV = os.getenv("ENVIRONMENT", "dev")

if ENV == "production":
    from .production import *
elif ENV == "staging":
    from .staging import *
else:
    from .dev import *