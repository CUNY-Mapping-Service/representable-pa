import requests
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from main.models import Organization

FLASK_APP_URL = 'http://app-plus:8001'

# @login_required 
@csrf_exempt
def flask_proxy(request, slug):
    """
    Forwards requests to Flask app with user headers and organization metadata.
    
    Args: slug: Organization slug from URL
    """
    user = request.user

    # Extract the path after /partners/{slug}/
    full_path = request.get_full_path()
    path_after_org = full_path.split(f'/partners/{slug}/turf', 1)[1] 
    flask_url = f"{FLASK_APP_URL}{path_after_org}"

    # Copy all headers from the original request
    headers = {
        'X-Authenticated-User': '',
        'X-Org-Name': '',
        'X-Org-Id': '',
        'X-Org-Slug': '',
    }
    for key, value in request.headers.items():
        # Skip these headers
        if key.lower() not in ['host', 'connection', 'content-length']:
            headers[key] = value
    
    # Add/override with custom authentication headers
    if not user.is_anonymous:
        # Get the organization by slug
        organization = get_object_or_404(Organization, slug=slug)
        
        # Check if user is an admin of this organization
        if not user.is_org_admin(organization.id):
            return HttpResponseForbidden("You do not have permission to access this organization")
        
        headers.update({
            'X-Authenticated-User': user.username,
            'X-Authenticated-User-Id': str(user.id),
            'X-Org-Name': organization.name,
            'X-Org-Id': str(organization.id),
            'X-Org-Slug': organization.slug,
        })
    
    request_params = {
        'headers': headers,
        'timeout': 30
    }
    
    # Add body
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        request_params['data'] = request.body
        # Preserve Content-Type
        if 'Content-Type' in request.headers: 
                headers['Content-Type'] = request.headers['Content-Type']
    
    # Add query parameters
    if request.GET:
        request_params['params'] = request.GET
    
    try:
        response = requests.request(
            method=request.method,
            url=flask_url,
            **request_params
        )
        
        django_response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'text/html')
        )
        
        # Copy important headers
        headers_to_copy = [
            'Content-Type', 
            'Cache-Control', 
            'Set-Cookie',
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers',
        ]
        
        for header in headers_to_copy:
            if header in response.headers:
                django_response[header] = response.headers[header]
        
        return django_response
    
    except requests.Timeout:
        return HttpResponse("Request timed out", status=504)
    except requests.ConnectionError:
        return HttpResponse("Could not connect to Flask app", status=502)
    except requests.RequestException as e:
        return HttpResponse(f"Error connecting: {str(e)}", status=502)