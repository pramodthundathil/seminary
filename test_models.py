import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()
from home.models import ChurchLoginCodeSettings
print(dir(ChurchLoginCodeSettings))
