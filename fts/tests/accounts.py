# -*- coding: utf-8 -*-
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.utils.translation import ugettext
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class AccountsTest(LiveServerTestCase):
	fixtures = ['accounts_user.json']

	def setUp(self):
		self.browser = webdriver.Firefox()
		self.browser.implicitly_wait(5)

	def tearDown(self):
		self.browser.quit()

	def test_create_account_via_admin_site(self):
		self.browser.get(self.live_server_url + reverse('admin:index'))

		username_field = self.browser.find_element_by_name('username')
		username_field.send_keys('admin')

		password_field = self.browser.find_element_by_name('password')
		password_field.send_keys('pass')
		password_field.send_keys(Keys.RETURN)

		self.browser.get(self.live_server_url + reverse('admin:accounts_user_changelist'))
		user_rows = self.browser.find_elements_by_css_selector('#result_list tbody tr')
		self.assertEqual(len(user_rows), 1)

		self.browser.get(self.live_server_url + reverse('admin:accounts_user_add'))
		create_username_field = self.browser.find_element_by_name('username')
		create_username_field.send_keys('user2')

		create_password_field1 = self.browser.find_element_by_name('password1')
		create_password_field1.send_keys('password')

		create_password_field2 = self.browser.find_element_by_name('password2')
		create_password_field2.send_keys('password')
		create_password_field2.send_keys(Keys.RETURN)

		info_rows = self.browser.find_elements_by_css_selector('.messagelist .info')
		self.assertEqual(len(info_rows), 1)

	def test_user_registration(self):
		self.register_user()
		self.login_user()
		self.change_profile()
		self.logout()
		self.register_duplicate_mail()

	def register_user(self):
		self.browser.get(self.live_server_url + reverse('registration_register'))

		username_field = self.browser.find_element_by_name('username')
		username_field.send_keys('user')

		email_field = self.browser.find_element_by_name('email')
		email_field.send_keys('user@linuxos.sk')

		password_field1 = self.browser.find_element_by_name('password1')
		password_field1.send_keys('P4ssword')

		password_field2 = self.browser.find_element_by_name('password2')
		password_field2.send_keys('P4ssword')
		password_field2.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Registration complete"), body.text)

		self.assertEqual(len(mail.outbox), 1)

		message_body = str(mail.outbox[0].message())
		import re
		link_match = re.search('http(?s)://[^/]+([-\w/]*)', message_body)
		self.assertNotEqual(link_match, None)
		link = link_match.group(1)

		self.browser.get(self.live_server_url + link)
		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Your account is now active!"), body.text)

	def login_user(self):
		self.browser.get(self.live_server_url + reverse('home'))
		login_link = self.browser.find_element_by_link_text(ugettext("Log in"))
		login_link.click()

		username_field = self.browser.find_element_by_name('username')
		username_field.send_keys('user')

		password_field = self.browser.find_element_by_name('password')
		password_field.send_keys('P4ssword')
		password_field.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn("user", body.text)

	def change_profile(self):
		self.browser.get(self.live_server_url + reverse('auth_my_profile_edit'))
		self.profile_check_bad_password()
		self.profile_change_data()
		self.profile_change_email()
		self.profile_change_existing_email()
		self.profile_change_password()

	def profile_check_bad_password(self):
		password_field = self.browser.find_element_by_name('current_password')
		password_field.send_keys('BadP4ssword')
		password_field.send_keys(Keys.RETURN)

		errors = self.browser.find_elements_by_class_name('errorlist')
		self.assertEqual(len(errors), 1)

	def profile_change_data(self):
		password_field = self.browser.find_element_by_name('current_password')
		password_field.send_keys('P4ssword')

		first_name_field = self.browser.find_element_by_name('first_name')
		first_name_field.send_keys('John')

		last_name_field = self.browser.find_element_by_name('last_name')
		last_name_field.send_keys('Smith')
		last_name_field.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("User profile"), body.text)
		self.assertIn("John", body.text)
		self.assertIn("Smith", body.text)

	def profile_change_email(self):
		self.browser.get(self.live_server_url + reverse('auth_email_change'))

		password_field = self.browser.find_element_by_name('current_password')
		password_field.send_keys('P4ssword')

		email_field = self.browser.find_element_by_name('email')
		email_field.clear()
		email_field.send_keys('test@test.com')
		email_field.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("E-mail change request sent"), body.text)

		self.assertEqual(len(mail.outbox), 2)
		message_body = str(mail.outbox[1].message())
		import re
		link_match = re.search('http(?s)://[^/]+([-\w/]*)', message_body)
		self.assertNotEqual(link_match, None)
		link = link_match.group(1)

		self.browser.get(self.live_server_url + link)
		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("E-mail change complete"), body.text)

	def profile_change_existing_email(self):
		self.browser.get(self.live_server_url + reverse('auth_email_change'))

		password_field = self.browser.find_element_by_name('current_password')
		password_field.send_keys('P4ssword')

		email_field = self.browser.find_element_by_name('email')
		email_field.clear()
		email_field.send_keys('mireq@linuxos.sk')
		email_field.send_keys(Keys.RETURN)

		errors = self.browser.find_elements_by_class_name('errorlist')
		self.assertEqual(len(errors), 1)

	def logout(self):
		self.browser.get(self.live_server_url + reverse('auth_logout'))
		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Logged out"), body.text)

	def register_duplicate_mail(self):
		self.browser.get(self.live_server_url + reverse('registration_register'))

		username_field = self.browser.find_element_by_name('username')
		username_field.send_keys('user2')

		email_field = self.browser.find_element_by_name('email')
		email_field.send_keys('mireq@linuxos.sk')

		password_field1 = self.browser.find_element_by_name('password1')
		password_field1.send_keys('P4ssword')

		password_field2 = self.browser.find_element_by_name('password2')
		password_field2.send_keys('P4ssword')
		password_field2.send_keys(Keys.RETURN)

		errors = self.browser.find_elements_by_class_name('errorlist')
		self.assertEqual(len(errors), 1)

	def profile_change_password(self):
		self.browser.get(self.live_server_url + reverse('auth_password_change'))

		password_field = self.browser.find_element_by_name('old_password')
		password_field.send_keys('P4ssword')

		password_field1 = self.browser.find_element_by_name('new_password1')
		password_field1.send_keys('P4ssword2')

		password_field2 = self.browser.find_element_by_name('new_password2')
		password_field2.send_keys('P4ssword2')
		password_field2.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Password change successful"), body.text)

	def test_password_reset(self):
		self.browser.get(self.live_server_url + reverse('auth_password_reset'))

		email_field = self.browser.find_element_by_name('email')
		email_field.send_keys('mireq@linuxos.sk')
		email_field.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Password reset successful"), body.text)

		self.assertEqual(len(mail.outbox), 1)

		message_body = str(mail.outbox[0].message())
		import re
		link_match = re.search('http(?s)://[^/]+([-\w/]*)', message_body)
		self.assertNotEqual(link_match, None)
		link = link_match.group(1)

		self.browser.get(self.live_server_url + link)
		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Password reset"), body.text)

		password_field1 = self.browser.find_element_by_name('new_password1')
		password_field1.send_keys('P4ssword2')

		password_field2 = self.browser.find_element_by_name('new_password2')
		password_field2.send_keys('P4ssword2')
		password_field2.send_keys(Keys.RETURN)

		body = self.browser.find_element_by_tag_name('body')
		self.assertIn(ugettext("Password reset complete"), body.text)