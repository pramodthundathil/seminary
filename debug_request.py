import os
import django
import sys
# Setup Django environment
sys.path.append('/Users/pramodgopinath/Desktop/Trinity_Seminary/seminary')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from menu.views import student_books_datatable
from home.models import Users

def run_test():
    factory = RequestFactory()
    request = factory.get('/menu/students/books/datatable/')
    
    # Mock user
    user = Users.objects.first()
    request.user = user
    
    try:
        response = student_books_datatable(request)
        print(f"Status Code: {response.status_code}")
        print(f"Content: {response.content.decode('utf-8')[:500]}...") # Print first 500 chars
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    run_test()
