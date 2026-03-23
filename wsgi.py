import os
import sys
from pathlib import Path
import pymysql

# Configure PyMySQL to work with Django
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Add the project directory to Python path
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'placement_django_backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_django_backend.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()