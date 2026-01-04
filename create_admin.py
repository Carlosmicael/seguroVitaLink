#!/usr/bin/env python
"""
Script temporal para crear un superusuario de Django
Ejecutar: python create_admin.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superusuario si no existe
username = 'admin'
email = 'admin@vitalink.utpl.edu.ec'
password = 'admin123'  # Cambiar después

if User.objects.filter(username=username).exists():
    print(f'El usuario "{username}" ya existe.')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'✓ Superusuario creado exitosamente!')
    print(f'  Usuario: {username}')
    print(f'  Contraseña: {password}')
    print(f'\n⚠️  IMPORTANTE: Cambia la contraseña después del primer inicio de sesión!')

