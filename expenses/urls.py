from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Home page/dashboard
    path('add/', views.add_transaction, name='add_transaction'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('search/', views.search_transactions, name='search_transactions'),
    # Add more routes as needed
]