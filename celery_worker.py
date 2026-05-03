import os
from dotenv import load_dotenv

load_dotenv()

from tuned import create_app

flask_env = os.environ.get('FLASK_ENV', 'development')
app = create_app(flask_env)
celery_app = app.extensions['celery']
