# panel_asesor/utils.py
import random
import string
from django.contrib.auth.models import User

def generar_usuario(nombre, apellido):
    base = f"{nombre[0]}{apellido}".lower().replace(" ", "")
    contador = 1

    while True:
        username = f"{base}{contador}"
        if not User.objects.filter(username=username).exists():
            return username
        contador += 1

def generar_password():
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(random.choice(caracteres) for _ in range(10))
    return password

