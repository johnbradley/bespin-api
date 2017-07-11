from rest_framework.views import exception_handler
from renderers import JSONRootObjectRenderer


def switching_exception_handler(exc, context):
    request = context.get('request')
    handler = exception_handler
    if request.accepted_media_type == JSONRootObjectRenderer.media_type:
        handler = json_root_object_exception_handler
    return handler(exc, context)


def make_json_root_error(status_code, data, exc):
    # JSON root errors should conform to JSONAPI: http://jsonapi.org/format/#error-objects
    error = { 'status': status_code }
    if isinstance(data, str):
        error['detail'] = data
    elif isinstance(data, dict):
        error['detail'] = data.get('detail')
        if data.get('id'):
            error['id'] = data.get('id')
    return error


def json_root_object_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    # response.data may be a list or a single object

    if isinstance(response.data, list):
        errors = [make_json_root_error(response.status_code, data, exc) for data in response.data]
    else:
        errors = [make_json_root_error(response.status_code, response.data, exc)]

    response.data = {'errors': errors}
    return response
