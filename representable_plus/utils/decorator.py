from flask import request
from functools import wraps

def with_user_info(f):
    """Extracts user information from headers and passes it to the route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_name = request.headers.get('X-Authenticated-User', 'Guest')
        user_id = request.headers.get('X-Authenticated-User-Id', None)
        org_name = request.headers.get('X-Org-Name', 'Guest')
        org_id = request.headers.get('X-Org-Id', None)
        
        # Add user info to kwargs
        kwargs['user_name'] = user_name
        kwargs['user_id'] = user_id
        kwargs['org_name'] = org_name
        kwargs['org_id'] = org_id
        
        return f(*args, **kwargs)
    return decorated_function