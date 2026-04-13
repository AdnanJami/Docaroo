from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update-profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('google/', views.GoogleLoginView.as_view(), name='google-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dashboard/customer/', views.CustomerDashboardView.as_view(), name='customer-dashboard'),
    path('admin/toggle-editable/<int:user_id>/', views.ToggleEditableView.as_view(), name='toggle-editable'),  
    path('admin/delete-customer/<int:user_id>/', views.DeleteCustomerView.as_view(), name='delete-customer'),
    path('profile/delete/', views.DeleteOwnAccountView.as_view(), name='delete-own-account'),
]