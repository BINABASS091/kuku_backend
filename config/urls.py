"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
# Temporarily remove this import to fix circular dependency
# from .views import APIRootView

from rest_framework_simplejwt.views import TokenRefreshView  # type: ignore
from accounts.auth import RoleTokenObtainPairView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView  # type: ignore

# API URLS (grouped for clarity)
api_patterns = [
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication
    path('api/token/', RoleTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API v1
    path('api/v1/', include('config.v1_urls')),
]

urlpatterns = [
    # Temporarily comment out APIRootView due to circular import
    # path('', APIRootView.as_view(), name='root'),
    path('admin/', admin.site.urls),
    *api_patterns,
]

# Include debug toolbar URLs only in development
if settings.DEBUG:
    try:
        import debug_toolbar  # type: ignore
    except ImportError:
        debug_toolbar = None  # Optional dependency
    else:
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
