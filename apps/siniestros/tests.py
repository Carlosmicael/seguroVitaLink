from django.test import TestCase
from django.contrib.auth.models import User
from .models import Poliza, Siniestro


class PolizaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.poliza = Poliza.objects.create(
            numero='VL-2026-001',
            usuario=self.user,
            estado='activa'
        )
    
    def test_poliza_creation(self):
        self.assertEqual(self.poliza.numero, 'VL-2026-001')
        self.assertEqual(self.poliza.estado, 'activa')
    
    def test_poliza_str(self):
        expected_str = f"Póliza {self.poliza.numero} - {self.poliza.estado}"
        self.assertEqual(str(self.poliza), expected_str)


class SiniestroModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.poliza = Poliza.objects.create(
            numero='VL-2026-001',
            usuario=self.user
        )
        self.siniestro = Siniestro.objects.create(
            poliza=self.poliza,
            tipo='accidente',
            descripcion='Accidente automovilístico',
            fecha_evento='2026-01-02'
        )
    
    def test_siniestro_creation(self):
        self.assertEqual(self.siniestro.tipo, 'accidente')
        self.assertEqual(self.siniestro.estado, 'pendiente')
