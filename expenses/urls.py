"""App-specific URL patterns for expenses views."""

from django.urls import path

from . import views


app_name = 'expenses'


urlpatterns = [
    # Dashboard combines quick stats, charts, and transaction capture.
    path('', views.dashboard, name='dashboard'),
    # Dedicated list page to scroll through historical transactions.
    path('transactions/', views.transaction_list, name='transaction_list'),
]