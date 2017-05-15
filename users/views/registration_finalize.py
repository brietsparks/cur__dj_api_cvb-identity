from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from users.models import User
from ..services import Profiles, Emails
from ..tokens import Jwt
from ..models import User
import jwt


@api_view(['POST'])
def registration_finalize(request):
    response_data = {
        'claimTokenInvalid': not _request_has_valid_claim_token(request),
        'passwordInvalid': not _request_has_valid_password(request),
        'authToken': None
    }

    if response_data['claimTokenInvalid'] or response_data['passwordInvalid']:
        return Response(response_data, status.HTTP_400_BAD_REQUEST)

    # todo: authenticate and return authToken
    token_data = Jwt(encoded=request.data['claimToken']).decode()
    if 'profile_uuid' not in token_data:
        profile_uuid = Profiles.create_new_profile(token_data['email'])
    else:
        profile_uuid = request.data['profile_uuid']

    user = User.objects.create(
        email=request.data['email'],
        password=request.data['password'],
        profile_uuid=profile_uuid
    )


def _request_has_valid_claim_token(request):
    return True  # todo


def _request_has_valid_password(request):
    return True # todo

