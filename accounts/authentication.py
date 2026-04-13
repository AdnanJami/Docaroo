from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken


class BlacklistCheckJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result

        try:
            jti = validated_token['jti']
            outstanding = OutstandingToken.objects.get(jti=jti)
            if BlacklistedToken.objects.filter(token=outstanding).exists():
                raise InvalidToken('Access token has been blacklisted.')
        except OutstandingToken.DoesNotExist:
            pass  # Token not in outstanding list, allow it

        return user, validated_token