from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from users.models import User
from ..services import Profiles, Emails
from ..tokens import Jwt

CLAIM_TOKEN_DURATION_SECONDS = 600


@api_view(['POST'])
def registration_initialize(request):
    # initial response data, which gets changed throughout the procedure
    response_data = {
        'emailInvalid': not _request_has_valid_email(request),
        'usernameInvalid': not _request_has_valid_username(request),
        'emailClaimed': None,
        'usernameClaimed': None,
        'profileExists': None,
        'claimToken': None
    }

    # if data is invalid, return a 400
    if response_data['emailInvalid'] or response_data['usernameInvalid']:
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    username = request.data['username']
    email = request.data['email']

    # check if the user exists
    response_data['emailClaimed'] = User.objects.filter(email=email).exists()
    response_data['usernameClaimed'] = User.objects.filter(username=username).exists()

    # if either the email or username is taken, return a 400
    if response_data['emailClaimed'] or response_data['usernameClaimed']:
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # at this point the email/username combination is available
    # create a claim token, which locks in the chose email/username combination
    response_claim_token = Jwt.create_token(
        duration_seconds=CLAIM_TOKEN_DURATION_SECONDS,
        email=email, username=username)
    response_data['claimToken'] = response_claim_token

    # check if the email is linked to an existing Profile
    profile_uuid = Profiles.get_profile_uuid_by_email_or_none(email)
    response_data['profileExists'] = profile_uuid is not None

    # if email is linked to an existing Profile, send a separate claim token to the email
    if response_data['profileExists']:
        email_claim_token = Jwt.create_token(
            duration_seconds=CLAIM_TOKEN_DURATION_SECONDS,
            profileUuid=profile_uuid, email=email, username=username
        )
        Emails.send_account_claim_token_email(email, email_claim_token)

    # return a 200 containing the built-up response data
    return Response(response_data)


def _request_has_valid_email(request):
    data = request.data
    if 'email' not in data:
        return False
    try:
        validate_email(data['email'])
        return True
    except ValidationError:
        return False


def _request_has_valid_username(request):
    data = request.data
    return 'username' in data and \
           data['username'] is not None and \
           len(request.data['username']) > 2
