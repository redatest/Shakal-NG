# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.functional import cached_property
from django.db.models.signals import post_save, pre_save, pre_delete
from django.contrib.auth.signals import user_logged_out
from .auth_remember_utils import preset_cookie


class AccountsConfig(AppConfig):
	name = 'accounts'
	verbose_name = 'Používateľské kontá'

	RATING_WEIGHTS = {
		'comments': 1,
		'articles': 200,
		'helped': 20,
		'news': 10,
		'wiki': 50,
	}

	@cached_property
	def senders(self):
		from article.models import Article
		from news.models import News
		from threaded_comments.models import Comment
		from wiki.models import Page as WikiPage

		return {
			Comment: ('user', 'comments', lambda c: c.is_public and not c.is_removed),
			News: ('author', 'news', lambda c: c.approved),
			WikiPage: ('last_author', 'wiki', lambda c: True),
			Article: ('author', 'articles', lambda c: c.published),
		}

	def update_user_rating(self, instance, author_property, property_name, change):
		user = getattr(instance, author_property)
		if user:
			rating = self.get_model('UserRating').objects.get_or_create(user=user)[0]
			setattr(rating, property_name, max(getattr(rating, property_name) + change, 0))
			rating.rating = sum(getattr(rating, w[0]) * w[1] for w in self.RATING_WEIGHTS.iteritems())
			rating.save()

	def update_count_post_save(self, sender, instance, **kwargs):
		if not sender in self.senders:
			return
		author_property, property_name, count_fun = self.senders[sender]
		self.update_user_rating(instance, author_property, property_name, int(count_fun(instance)))

	def update_count_pre_save(self, sender, instance, **kwargs):
		if not sender in self.senders:
			return
		author_property, property_name, count_fun = self.senders[sender]
		if instance.pk:
			try:
				instance = instance.__class__.objects.get(pk=instance.pk)
				self.update_user_rating(instance, author_property, property_name, -int(count_fun(instance)))
			except instance.__class__.DoesNotExist:
				pass

	def remove_auth_token(self, sender, **kwargs): #pylint: disable=unused-argument
		request = kwargs['request']
		user = request.user
		preset_cookie(request, '')
		RememberToken = self.get_model('RememberToken')
		RememberToken.objects.all().filter(user=user).delete()

	def set_inactive(self, request, user, **kwargs): #pylint: disable=unused-argument
		user.is_active = False
		user.is_staff = False
		user.save()

	def set_active(self, request, email_address, **kwargs): #pylint: disable=unused-argument
		user = email_address.user
		user.is_active = True
		user.save()

	def set_registration_active(self):
		from allauth.account.signals import user_signed_up, email_confirmed
		user_signed_up.connect(self.set_inactive)
		email_confirmed.connect(self.set_active)

	def ready(self):
		pre_save.connect(self.update_count_pre_save)
		pre_delete.connect(self.update_count_pre_save)
		post_save.connect(self.update_count_post_save)
		user_logged_out.connect(self.remove_auth_token)
		self.set_registration_active()
