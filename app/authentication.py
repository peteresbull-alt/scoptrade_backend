from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieTokenAuthentication(TokenAuthentication):
    """
    Custom authentication that reads the token from an HTTPOnly cookie
    instead of the Authorization header.
    """

    def authenticate(self, request):
        token = request.COOKIES.get('access_token')
        if not token:
            return None

        return self.authenticate_credentials(token)
