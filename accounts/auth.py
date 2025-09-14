"""Custom JWT token views adding role and redirect hint.

Ensure the virtual environment is active so imports resolve.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore
from rest_framework_simplejwt.views import TokenObtainPairView  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend default token serializer to include role and basic user info."""

    @classmethod
    def get_token(cls, user):
        tok = super().get_token(user)
        role = getattr(user, 'role', None)
        if isinstance(role, str):
            role_lc = role.lower()
        else:
            role_lc = role
        tok['role'] = role_lc
        tok['is_staff'] = user.is_staff
        tok['is_superuser'] = user.is_superuser
        return tok

    def validate(self, attrs):
        data = super().validate(attrs)
        role = getattr(self.user, 'role', None)
        norm_role = role.lower() if isinstance(role, str) else role
        data.update({
            'username': self.user.username,
            'role': norm_role,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'redirect': '/admin' if norm_role == 'admin' else '/dashboard'
        })
        return data


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer

__all__ = ['RoleTokenObtainPairSerializer', 'RoleTokenObtainPairView']
