from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

password_hasher = PasswordHasher()

def make_hash(value: str) -> str:
    return password_hasher.hash(value)

def verify_hash(compared: str, value: str) -> bool:
    try:
        return password_hasher.verify(compared, value)
    except VerifyMismatchError:
        return False