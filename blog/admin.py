# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db import models
from django.template.loader import render_to_string

from attachment.admin import AttachmentInline
from blog.models import Blog, Post
from common_utils.admin_widgets import DateTimeInput


class BlogAdmin(admin.ModelAdmin):
	list_display = ('title', 'author',)
	search_fields = ('title', 'slug', 'author', )
	ordering = ('-id',)
	raw_id_fields = ('author',)
	prepopulated_fields = {'slug': ('title', )}


class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'get_status')
	search_fields = ('title', 'slug', )
	ordering = ('-id',)
	raw_id_fields = ('blog', )
	prepopulated_fields = {'slug': ('title', )}
	inlines = [AttachmentInline]
	date_hierarchy = 'pub_time'
	formfield_overrides = {
		models.DateTimeField: { 'widget': DateTimeInput }
	}

	def get_status(self, obj):
		if obj.published():
			cls = "success"
			text = u"Publikovaný"
		else:
			cls = "warning"
			text = u"Čaká na publikovanie"
		ctx = {'cls': cls, 'text': text, 'star': obj.linux}
		return render_to_string('admin/partials/label_star.html', ctx)
	get_status.short_description = u"Stav"
	get_status.allow_tags = True


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
