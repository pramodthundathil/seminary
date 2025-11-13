import bcrypt
from django.contrib.auth.backends import ModelBackend
from .models import Users

class LaravelBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return None

        # Compare Laravel bcrypt hash with entered password
        if user.password and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user
        return None
