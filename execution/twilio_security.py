import os
from twilio.request_validator import RequestValidator
from functools import wraps
from flask import request, abort, current_app

def validate_twilio_request(f):
    """
    Decorator that verifies if the request really came from Twilio.
    CRITICAL for production security.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # The X-Twilio-Signature header
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Twilio Auth Token from .env
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not auth_token:
            current_app.logger.error("TWILIO_AUTH_TOKEN not set in environment")
            abort(500)

        validator = RequestValidator(auth_token)

        # In production, we must use the full URL including scheme
        # Passenger/cPanel often sits behind a proxy, so we check X-Forwarded-Proto
        url = request.url
        if request.headers.get('X-Forwarded-Proto') == 'https':
            url = url.replace('http:', 'https:')

        # Validate the request
        if not validator.validate(url, request.form, signature):
            print(f"!!! SECURITY ALERT: Invalid Twilio Signature")
            print(f"    URL: {url}")
            print(f"    Signature: {signature}")
            current_app.logger.warning(f"Invalid Twilio Signature from {request.remote_addr}")
            abort(403)
        
        print("    Security: Twilio Signature Verified.")
        return f(*args, **kwargs)
    return decorated_function
