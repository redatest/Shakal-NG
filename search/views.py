# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from haystack.views import SearchView as HaystackSearchView

from .forms import SearchForm
from paginator.utils import paginate_queryset


class SearchView(HaystackSearchView):
	paginate_by = 20

	def __init__(self, *args, **kwargs):
		if not 'form_class' in kwargs:
			kwargs['form_class'] = SearchForm
		super(SearchView, self).__init__(*args, **kwargs)

	def create_response(self):
		queryset = self.results
		paginator, page, queryset, is_paginated = paginate_queryset(queryset, self.request.GET.get('page') or 1, self.paginate_by)

		context = {
			'query': self.query,
			'form': self.form,
			'suggestion': None,
			'paginator': paginator,
			'page_obj': page,
			'results': queryset,
			'is_paginated': is_paginated,
		}

		if self.results and hasattr(self.results, 'query') and self.results.query.backend.include_spelling:
			context['suggestion'] = self.form.get_suggestion()

		context.update(self.extra_context())
		return render_to_response(self.template, context, context_instance=self.context_class(self.request))
