# exams/debug_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import UntypedToken
import jwt
from django.conf import settings

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    out = {
        'http_authorization': auth_header,
        'request_user': str(request.user),
        'user_is_authenticated': request.user.is_authenticated,
    }

    if auth_header and len(auth_header.split()) == 2:
        token = auth_header.split()[1]
        out['token_raw_preview'] = token[:20] + '...'
        try:
            UntypedToken(token)
            out['token_valid'] = True
            try:
                out['decoded_payload'] = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=['HS256'], options={'verify_exp': False}
                )
            except Exception as e:
                out['decoded_payload_error'] = repr(e)
        except Exception as e:
            out['token_valid'] = False
            out['token_error'] = repr(e)
    else:
        out['token_present'] = False

    return Response(out)
