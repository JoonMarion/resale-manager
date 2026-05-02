from django.contrib.auth.mixins import LoginRequiredMixin


class ProjectLoginRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure that the user is authenticated.
    Can be extended later for tenant or permission checks.
    """
    login_url = '/login/'
    redirect_field_name = 'next'
