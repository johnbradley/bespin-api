from gcb_web_auth import views as gcb_auth_views
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
import json
import urllib


def authorize(request):
    service = gcb_auth_views.get_service(request)
    if service is None:
        return redirect('auth-unconfigured')
    auth_url, state_string = gcb_auth_views.authorization_url(service)
    # Save the state with the next parameter if provided
    gcb_auth_views.push_state(request, state_string)
    return redirect(auth_url)


def authorize_callback(request):
    destination = gcb_auth_views.pop_state(request)
    service = gcb_auth_views.get_service(request)
    # This gets the token dictionary from the callback URL
    token_dict = gcb_auth_views.get_token_dict(service, request.build_absolute_uri())
    # Determine identity of the user, using the token
    user = authenticate(service=service, token_dict=token_dict)
    if user:
        gcb_auth_views.save_token(service, token_dict, user)
        login(request, user)
        resp = redirect('/')
        if destination:
            resp = redirect(destination)
        resp.set_cookie('bespinsession', create_bespin_session_cookie_value(user))
        return resp

    else:
        return redirect('/')


def create_bespin_session_cookie_value(user):
    """
    Creates a cookie containing a token for the specified user in the format that is needed by bespin-ui.
    Creates a token if the user doesn't currently have one.
    :param user: User: django user we will create a cookie for
    :return: str: cookie value
    """
    token, created = Token.objects.get_or_create(user=user)
    auth_data = {"authenticated": {"authenticator": "authenticator:drf-token-authenticator", "token": token.key}}
    json_auth_data = json.dumps(auth_data)
    return urllib.quote(json_auth_data)
