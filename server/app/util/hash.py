from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

password_hasher = PasswordHasher()

class Hasher:
    @staticmethod
    def make(value: str) -> str:
        return password_hasher.hash(value)
    
    @staticmethod
    def verify(compared: str, value: str) -> bool:
        try:
            return password_hasher.verify(compared, value)
        except VerifyMismatchError:
            return False