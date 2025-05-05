import random
import string

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))