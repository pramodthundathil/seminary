from django.contrib.auth.backends import ModelBackend
from .models import Users

class LaravelBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Users.objects.get(email__iexact=email)
        except Users.DoesNotExist:
            return None

        # Compare hash with entered password using custom check_password method
        if user.password and user.check_password(password):
            return user
        return None

