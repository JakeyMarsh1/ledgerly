"""Project URL routing for Ledgerly, annotated per entry."""
from django.urls import path, include
from expenses import views
from expenses.admin import ledgerly_admin_site
from expenses.views_login import NoNextLoginView

urlpatterns = [
    # Django admin for managing data when needed.
    path('admin/', ledgerly_admin_site.urls),
    # Primary dashboard landing page for authenticated users.
    path('', views.dashboard, name='dashboard'),
    # Full transaction history plus detail/edit/delete flows.
    path('transactions/', views.transaction_list, name='transaction_list'),
    path(
        'transactions/<int:pk>/',
        views.transaction_detail,
        name='transaction_detail',
    ),
    path(
        'transactions/<int:pk>/delete/',
        views.transaction_delete,
        name='transaction_delete',
    ),
    path(
        'transactions/calendar-data/',
        views.transaction_calendar_data,
        name='transaction_calendar_data',
    ),
    path(
        'transactions/search-results/',
        views.transaction_search_results,
        name='transaction_search_results',
    ),
    path(
        'transactions/suggestions/',
        views.transaction_suggestions,
        name='transaction_suggestions',
    ),
    # Allow users to delete their account via confirmation page.
    path('accounts/delete/', views.delete_account, name='account_delete'),
    path(
        'accounts/clear-history/',
        views.clear_history,
        name='account_clear_history',
    ),
    path(
        'accounts/currency/',
        views.currency_settings,
        name='account_currency_settings',
    ),
    # Bypass allauth's intermediate logout page and immediately redirect
    # users back to the login form.
    path('accounts/logout/', views.custom_logout, name='account_logout'),
    # Override login to remove ?next=/ if present.
    path('accounts/login/', NoNextLoginView.as_view(), name='account_login'),
    # Include allauth's account management routes (login, signup, etc.).
    path('accounts/', include('allauth.urls')),
]
