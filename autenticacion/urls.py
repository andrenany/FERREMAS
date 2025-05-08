from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoints de registro
    path('register/cliente/', UserViewSet.as_view({'post': 'create_cliente'}), name='register-cliente'),
    path('register/staff/', UserViewSet.as_view({'post': 'create_staff'}), name='register-staff'),
    path('register/admin/', UserViewSet.as_view({'post': 'create_admin'}), name='register-admin'),
    
    # Gestión de contraseñas
    path('password/change/<int:pk>/', UserViewSet.as_view({'post': 'change_password'}), name='password-change'),
    path('password/reset/', UserViewSet.as_view({'post': 'reset_password'}), name='password-reset'),
    path('password/reset/confirm/', UserViewSet.as_view({'post': 'reset_password_confirm'}), name='password-reset-confirm'),
    
    # Newsletter
    path('newsletter/', UserViewSet.as_view({'post': 'toggle_newsletter'}), name='newsletter'),
    
    # Perfil de usuario
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-profile'),
] 