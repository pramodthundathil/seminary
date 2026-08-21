import os
import sys
import django
from django.db import connection
from django.core.management import call_command

# Dynamic path resolution to support both local and remote environments
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

table_names = connection.introspection.table_names()

print("Disabling all database triggers/constraints...")
with connection.cursor() as cursor:
    for table in table_names:
        try:
            cursor.execute(f'ALTER TABLE "{table}" DISABLE TRIGGER ALL;')
        except Exception as e:
            print(f"Could not disable triggers for table {table}: {e}")

try:
    print("Loading database fixture (complete_data.json)...")
    call_command('loaddata', 'complete_data.json', verbosity=2)
    print("Fixture loaded successfully!")
except Exception as e:
    print(f"Error loading fixture: {e}")
finally:
    print("Re-enabling all database triggers/constraints...")
    with connection.cursor() as cursor:
        for table in table_names:
            try:
                cursor.execute(f'ALTER TABLE "{table}" ENABLE TRIGGER ALL;')
            except Exception as e:
                print(f"Could not enable triggers for table {table}: {e}")

print("Done!")
