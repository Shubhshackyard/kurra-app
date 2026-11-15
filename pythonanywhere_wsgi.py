"""PythonAnywhere WSGI Configuration for Kurra Cadastral System.

Uses SingleThreadASGItoWSGI to execute FastAPI synchronously without uWSGI GIL deadlocks.
"""
import sys
import os

project_home = '/home/quirkyzillionaire/kurra-app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load secrets from local .env file
env_file = os.path.join(project_home, '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

# Mount FastAPI via SingleThreadASGItoWSGI
from kurra.api.main import app as fastapi_app
from kurra.wsgi_adapter import SingleThreadASGItoWSGI

application = SingleThreadASGItoWSGI(fastapi_app)
