# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class EventManager(models.Manager):
	def __get_active_users(self):
		return get_user_model().objects.filter(is_active = True)

	def __generate_inbox_objects(self, users, event_id):
		user_ids = users.values_list('pk', flat = True)
		for user_id in user_ids:
			yield Inbox(event_id = event_id, recipient_id = user_id)

	def create_event(self, message, content_object, action, level, author):
		event = Event(author = author)
		if content_object is not None:
			event.object_id = content_object.pk
			event.content_type = ContentType.objects.get_for_model(content_object)
		if action:
			event.action = action
		if level:
			event.level = level
		event.message = message
		return event

	def filter_users(self, author, is_staff, is_superuser, permissions):
		users = self.__get_active_users()
		if author:
			users = users.exclude(pk = author.pk)
		if is_staff is not None:
			users = users.filter(is_staff = is_staff)
		if is_superuser is not None:
			users = users.filter(is_superuser = is_superuser)
		if permissions is not None:
			ct = ContentType.objects.get_for_model(permissions[0])
			perm = Permission.objects.get(content_type = ct, codename = permissions[1])
			users = users.filter(Q(user_permissions = perm) | Q(groups__permissions = perm) | Q(is_superuser = True)).distinct()
		return users

	def exclude_duplicate_events(self, users, event):
		if event.content_object:
			users = users.exclude(pk__in = get_user_model().objects.filter(Q(inbox__event__object_id = event.object_id) & Q(inbox__event__content_type_id = event.content_type_id) & Q(inbox__event__action = event.action) & Q(inbox__readed = False)))
		return users

	def notify_users(self, users, event):
		Inbox.objects.bulk_create(self.__generate_inbox_objects(users, event.pk))

	def broadcast(self, message, content_object = None, action = None, level = messages.INFO, author = None, users = None, is_staff = None, is_superuser = None, permissions = None):
		event = self.create_event(message, content_object, action, level, author)
		event.save()
		if users is None:
			users = self.filter_users(author, is_staff, is_superuser, permissions)
		users = self.exclude_duplicate_events(users, event)
		self.notify_users(users, event)

	def deactivate(self, content_object, action_type = None):
		events = Event.objects.filter(object_id = content_object.pk, content_type = ContentType.objects.get_for_model(content_object))
		if action_type is not None:
			events = events.filter(action = action_type)
		events.update(level = 0)


class Event(models.Model):
	OTHER_ACTION = 'x'
	CREATE_ACTION = 'c'
	UPDATE_ACTION = 'u'
	DELETE_ACTION = 'd'
	MESSAGE_ACTION = 'm'
	ADD_COMMENT_ACTION = 'a'

	ACTION_TYPE = (
		(OTHER_ACTION, _('other')),
		(CREATE_ACTION, _('create')),
		(UPDATE_ACTION, _('update')),
		(DELETE_ACTION, _('delete')),
		(MESSAGE_ACTION, _('message')),
		(ADD_COMMENT_ACTION, _('comment')),
	)

	objects = EventManager()

	object_id = models.PositiveIntegerField(blank = True, null = True)
	content_type = models.ForeignKey(ContentType, blank = True, null = True)
	time = models.DateTimeField(auto_now_add = True)
	content_object = generic.GenericForeignKey('content_type', 'object_id')
	action = models.CharField(max_length = 1, choices = ACTION_TYPE, default = MESSAGE_ACTION)
	level = models.IntegerField(default = messages.INFO)
	author = models.ForeignKey(settings.AUTH_USER_MODEL, blank = True, null = True)
	message = models.TextField()

	class Meta:
		index_together = [['object_id', 'content_type', 'action', 'level']]


class InboxManager(models.Manager):
	def user_messages(self, user):
		return self.get_queryset() \
			.select_related('event', 'event__content_type') \
			.filter(recipient = user) \
			.order_by('readed', '-pk')


class Inbox(models.Model):
	objects = InboxManager()

	recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name = 'inbox')
	event = models.ForeignKey(Event)
	readed = models.BooleanField(default = False)

	@property
	def content_type(self):
		if not self.event.content_type:
			return None
		return self.event.content_type.app_label + '.' + self.event.content_type.model

	@models.permalink
	def get_absolute_url(self):
		return ('notifications:read', None, {'pk': self.pk})
