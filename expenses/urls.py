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
    # I route the calendar data endpoint for the transaction calendar modal.
    path(
        'transactions/calendar-data/',
        views.transaction_calendar_data,
        name='transaction_calendar_data',
    ),
    # I route the search results endpoint for AJAX transaction searches.
    path(
        'search/',
        views.transaction_search_results,
        name='transaction_search_results',
    ),
]
