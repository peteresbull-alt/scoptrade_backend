"""
Custom JWT Authentication
Supports both HTTP-only cookies and Authorization header
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from HTTP-only cookies.
    Falls back to Authorization header if cookie not present.
    """

    def authenticate(self, request):
        # Priority 1: Try to get token from HTTP-only cookie
        raw_token = request.COOKIES.get('access_token')

        # Priority 2: If not in cookie, try Authorization header
        if not raw_token:
            header = self.get_header(request)
            if header is None:
                return None
            try:
                raw_token = self.get_raw_token(header)
            except Exception:
                return None

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, TokenError):
            # Token is invalid or expired — return None so AllowAny views
            # (login, register) can still proceed unauthenticated
            return None
        except AuthenticationFailed:
            raise
