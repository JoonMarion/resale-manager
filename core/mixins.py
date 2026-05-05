class SessionSortMixin:
    sort_param_name = 'sort'
    session_key_prefix = 'sort_'
    default_sort = None
    sort_options = {}  # format: {'value': 'ordering_string'}

    def get_sort_value(self):
        # 1. Check GET param
        sort_val = self.request.GET.get(self.sort_param_name)
        session_key = f"{self.session_key_prefix}{self.__class__.__name__}"
        
        if sort_val:
            # Save to session if valid
            if sort_val in self.sort_options:
                self.request.session[session_key] = sort_val
        else:
            # 2. Check session
            sort_val = self.request.session.get(session_key)
        
        # 3. Fallback to default
        if not sort_val or sort_val not in self.sort_options:
            sort_val = self.default_sort
            
        return sort_val

    def get_ordering(self):
        sort_val = self.get_sort_value()
        ordering = self.sort_options.get(sort_val)
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.get_sort_value()
        return context
