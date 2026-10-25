from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class EphemeralVercelTokenAuthentication(BaseAuthentication):
    """Signed demo tokens that work across isolated Vercel SQLite instances."""

    keyword = b"token"
    max_age_seconds = 60 * 60 * 24 * 30

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid authorization header.")

        try:
            username = signing.loads(
                parts[1].decode("utf-8"),
                salt="northstar.vercel-demo-token",
                max_age=self.max_age_seconds,
            )["username"]
            user = get_user_model().objects.get(username=username, is_active=True)
        except (signing.BadSignature, UnicodeDecodeError, KeyError, get_user_model().DoesNotExist) as exc:
            raise AuthenticationFailed("Invalid or expired token.") from exc
        return user, None

    def authenticate_header(self, request):
        return "Token"
