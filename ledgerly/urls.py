"""Project URL routing for Ledgerly, annotated per entry."""
from django.urls import path, include
from expenses import views
from expenses.admin import ledgerly_admin_site

urlpatterns = [
    # Django admin for managing data when needed.
    path('admin/', ledgerly_admin_site.urls),
    # Primary dashboard landing page for authenticated users.
    path('', views.dashboard, name='dashboard'),
    # Allow users to delete their account via confirmation page.
    path('accounts/delete/', views.delete_account, name='account_delete'),
    # Bypass allauth's intermediate logout page and immediately redirect
    # users back to the login form.
    path('accounts/logout/', views.custom_logout, name='account_logout'),
    # Include allauth's account management routes (login, signup, etc.).
    path('accounts/', include('allauth.urls')),
]
