import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare

class LaravelBCryptPasswordHasher(BasePasswordHasher):
    """
    Supports Laravel's bcrypt ($2y$) hashed passwords.
    """
    algorithm = "laravel_bcrypt"

    def verify(self, password, encoded):
        if not encoded.startswith("$2y$"):
            return False
        encoded_bcrypt = encoded.replace("$2y$", "$2b$")
        return constant_time_compare(
            bcrypt.hashpw(password.encode(), encoded_bcrypt.encode()).decode(),
            encoded_bcrypt
        )

    def encode(self, password, salt=None, iterations=None):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return hashed.decode().replace("$2b$", "$2y$")

    def safe_summary(self, encoded):
        return {"algorithm": self.algorithm, "hash": encoded[:10] + "..."}

    def must_update(self, encoded):
        return False
