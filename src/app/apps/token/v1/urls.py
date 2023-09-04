"""Warren Development app URLs configuration."""

from django.urls import path
from rest_framework_simplejwt import views

app_name = "token"

urlpatterns = [
    path("token/", views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token_refresh"),
]
