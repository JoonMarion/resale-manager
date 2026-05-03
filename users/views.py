from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .models import UserProfile


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/dashboard/'


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')


class ProfileView(LoginRequiredMixin, View):
    def _get_or_create_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self._get_or_create_profile(request.user)
        return render(request, 'users/profile.html', {'profile': profile})

    def post(self, request):
        profile = self._get_or_create_profile(request.user)
        store_name = request.POST.get('store_name', '').strip()
        store_phone = request.POST.get('store_phone', '').strip()
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        profile.store_name = store_name
        profile.store_phone = store_phone
        profile.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('users:profile')


class InAppPasswordChangeView(LoginRequiredMixin, View):
    def get(self, request):
        form = SetPasswordForm(user=request.user)
        return render(request, 'users/password_change.html', {'form': form})

    def post(self, request):
        form = SetPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # keep user logged in
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('users:profile')
        return render(request, 'users/password_change.html', {'form': form})
