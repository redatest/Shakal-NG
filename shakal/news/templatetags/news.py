# -*- coding: utf-8 -*-

from django import template
from shakal.news.models import News

register = template.Library()

@register.inclusion_tag('news/block_news_list.html')
def news_frontpage():
	return {'news': News.objects.filter(approved = True).order_by('-pk')[:15] }
