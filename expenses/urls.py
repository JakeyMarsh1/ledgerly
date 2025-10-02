"""I define the app-specific URL patterns for the expenses views."""

from django.urls import path

from . import views


app_name = 'expenses'


urlpatterns = [
    # I route the dashboard that combines quick stats, charts, and capture.
    path('', views.dashboard, name='dashboard'),
    # I route to the dedicated list page for historical transactions.
    path('transactions/', views.transaction_list, name='transaction_list'),
    # I route to the detail page for inspecting and editing a transaction.
    path(
        'transactions/<int:pk>/',
        views.transaction_detail,
        name='transaction_detail',
    ),
    # I route to the confirmation screen before deleting a transaction.
    path(
        'transactions/<int:pk>/delete/',
        views.transaction_delete,
        name='transaction_delete',
    ),
]
