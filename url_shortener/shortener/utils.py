import random
import string


ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 6


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    """Return a random alphanumeric string of `length` characters."""
    return "".join(random.choices(ALPHABET, k=length))