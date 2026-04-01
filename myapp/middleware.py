import logging

logger = logging.getLogger(__name__)

class DebugHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug(f"Incoming request headers: {request.headers}")
        logger.debug(f"Path: {request.path}")
        logger.debug(f"META headers: {request.META}")
        response = self.get_response(request)
        return response