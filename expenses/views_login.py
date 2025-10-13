
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView


class NoNextLoginView(LoginView):

    def get(self, request, *args, **kwargs):
        # Remove ?next=/ if present.
        # This avoids showing /accounts/login/?next=/ when not needed.
        if request.GET.get('next', None) == '/':
            return redirect('account_login')
        return super().get(request, *args, **kwargs)
    template_name = "account/login.html"
