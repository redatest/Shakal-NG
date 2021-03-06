# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

import views as wiki_views


class Patterns(object):
	def __init__(self):
		self.app_name = 'wiki'
		self.name = 'wiki'

	@property
	def urls(self):
		urlpatterns = patterns('wiki.views',
			url(r'^$', wiki_views.show_page, name = 'home'),
			url(r'(?P<slug>[-\w]+)/create/$', wiki_views.PageCreateView.as_view(), {'create': True}, name = 'create'),
			url(r'(?P<slug>[-\w]+)/edit/$', wiki_views.PageUpdateView.as_view(), {'create': False}, name = 'edit'),
			url(r'(?P<slug>[-\w]+)/history/(?P<history>\d+)/$', wiki_views.show_page, name = 'page-history'),
			url(r'(?P<slug>[-\w]+)/history/(?P<history>\d+)/(?P<page>\d+)/$', wiki_views.show_page, name = 'page-history-page'),
			url(r'(?P<slug>[-\w]+)/(?:(?P<page>\d+)/)?$', wiki_views.show_page, name = 'page'),
		)
		return (urlpatterns, self.app_name, self.name)

urlpatterns = Patterns().urls
