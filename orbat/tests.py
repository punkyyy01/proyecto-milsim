from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Regimiento, Compania, Peloton, Escuadra, Miembro


class ModelTests(TestCase):
	def test_regimiento_str_and_total_efectivos(self):
		r = Regimiento.objects.create(nombre="Test Reg", comandante="CO")
		c = Compania.objects.create(nombre="Alpha", regimiento=r)
		p = Peloton.objects.create(nombre="1er", compania=c)
		s = Escuadra.objects.create(nombre="Esc 1", peloton=p)
		Miembro.objects.create(nombre_milsim="Usuario1", rango="PV1", escuadra=s)

		self.assertEqual(str(r), "Test Reg")
		self.assertEqual(r.total_efectivos(), 1)


class OrbatViewTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_orbat_requires_login(self):
		resp = self.client.get('/orbat/')
		self.assertEqual(resp.status_code, 302)

	def test_orbat_view_logged_in(self):
		user = User.objects.create_user(username='u', password='p')
		self.client.login(username='u', password='p')

		r = Regimiento.objects.create(nombre="R", comandante="CO")
		c = Compania.objects.create(nombre="C", regimiento=r)
		p = Peloton.objects.create(nombre="P", compania=c)
		s = Escuadra.objects.create(nombre="S", peloton=p)
		Miembro.objects.create(nombre_milsim="Oper", rango="PV1", escuadra=s)

		resp = self.client.get('/orbat/')
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "R")
