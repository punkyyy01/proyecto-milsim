from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
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


class AdminSecurityTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.staff = User.objects.create_user(username='staff_user', password='p', is_staff=True)
		self.target = User.objects.create_user(username='target_user', password='p', is_staff=True)
		self.superuser = User.objects.create_superuser(username='root', password='p', email='root@example.com')

	def test_staff_cannot_access_admin_password_change(self):
		self.client.login(username='staff_user', password='p')
		response = self.client.get(reverse('admin:password_change'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('admin:index'))

	def test_superuser_can_access_admin_password_change(self):
		self.client.login(username='root', password='p')
		response = self.client.get(reverse('admin:password_change'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('admin:index'))

	def test_staff_sees_users_section_but_cannot_edit_users(self):
		self.client.login(username='staff_user', password='p')
		index_response = self.client.get(reverse('admin:index'))
		self.assertEqual(index_response.status_code, 200)
		self.assertContains(index_response, 'Usuarios')

		change_url = reverse('admin:auth_user_change', args=[self.target.id])
		change_response = self.client.post(
			change_url,
			{
				'username': 'hacked_username',
				'is_active': 'on',
				'is_staff': 'on',
				'is_superuser': '',
				'date_joined_0': '2026-01-01',
				'date_joined_1': '00:00:00',
			},
		)
		self.assertIn(change_response.status_code, [302, 403])
		self.target.refresh_from_db()
		self.assertEqual(self.target.username, 'target_user')

	def test_superuser_cannot_edit_users_from_admin_ui(self):
		self.client.login(username='root', password='p')
		change_url = reverse('admin:auth_user_change', args=[self.target.id])
		change_response = self.client.post(
			change_url,
			{
				'username': 'root_changed_username',
				'is_active': 'on',
				'is_staff': 'on',
				'is_superuser': '',
				'date_joined_0': '2026-01-01',
				'date_joined_1': '00:00:00',
			},
		)
		self.assertIn(change_response.status_code, [302, 403])
		self.target.refresh_from_db()
		self.assertEqual(self.target.username, 'target_user')

	def test_navbar_does_not_expose_user_change_link(self):
		self.client.login(username='staff_user', password='p')
		response = self.client.get(reverse('admin:index'))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'title="Edit profile"')
		self.assertNotContains(response, 'fa-user-edit')


class AuditLogTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.staff = User.objects.create_user(username='audit_staff', password='p', is_staff=True)
		self.staff_2 = User.objects.create_user(username='audit_staff_2', password='p', is_staff=True)
		self.normal = User.objects.create_user(username='normal_user', password='p', is_staff=False)
		ct = ContentType.objects.get_for_model(Regimiento)
		self.entry = LogEntry.objects.create(
			user=self.staff,
			content_type=ct,
			object_id='1',
			object_repr='Regimiento Test',
			action_flag=ADDITION,
			change_message='[{"added": {"name": "regimiento"}}]'
		)
		self.entry_other_user = LogEntry.objects.create(
			user=self.staff_2,
			content_type=ct,
			object_id='2',
			object_repr='Regimiento Global',
			action_flag=ADDITION,
			change_message='[{"added": {"name": "regimiento"}}]'
		)

	def test_staff_can_access_audit_list(self):
		self.client.login(username='audit_staff', password='p')
		response = self.client.get(reverse('audit_log_list'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Auditoría de cambios')
		self.assertContains(response, 'Regimiento Test')

	def test_staff_can_access_audit_detail(self):
		self.client.login(username='audit_staff', password='p')
		response = self.client.get(reverse('audit_log_detail', args=[self.entry.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Detalle de evento')
		self.assertContains(response, 'Regimiento Test')

	def test_non_staff_cannot_access_audit(self):
		self.client.login(username='normal_user', password='p')
		response = self.client.get(reverse('audit_log_list'))
		self.assertEqual(response.status_code, 302)

	def test_staff_can_export_audit_csv(self):
		self.client.login(username='audit_staff', password='p')
		response = self.client.get(reverse('audit_log_list'), {'export': 'csv'})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['Content-Type'], 'text/csv')
		self.assertIn('auditoria_orbat.csv', response['Content-Disposition'])
		self.assertContains(response, 'Regimiento Test')

	def test_staff_can_use_today_preset(self):
		self.client.login(username='audit_staff', password='p')
		response = self.client.get(reverse('audit_log_list'), {'preset': 'today'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Auditoría de cambios')

	def test_dashboard_recent_actions_is_global(self):
		self.client.login(username='audit_staff', password='p')
		response = self.client.get(reverse('admin:index'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Regimiento Global')

	def test_logentry_cannot_be_deleted(self):
		with self.assertRaises(PermissionDenied):
			self.entry.delete()
