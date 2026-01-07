import requests
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from main.models import Organization

FLASK_APP_URL = 'http://app-plus:8001'

# @login_required
def flask_proxy(request, slug):
    """
    Forwards requests to Flask app with user headers and organization metadata.
    
    Args: slug: Organization slug from URL
    """
    user = request.user

    # Extract the path after /partners/{slug}/
    # /partners/turf/test/ --> /
    full_path = request.get_full_path()
    path_after_org = full_path.split(f'/partners/{slug}/turf', 1)[1] 
    flask_url = f"{FLASK_APP_URL}/{path_after_org}"

    if not user.is_anonymous:
        # Get the organization by slug
        organization = get_object_or_404(Organization, slug=slug)
        
        # Check if user is an admin of this organization
        if not user.is_org_admin(organization.id):
            return HttpResponseForbidden("You do not have permission to access this organization")
        
        headers = {
            'X-Authenticated-User': user.username,
            'X-Org-Name': organization.name,
            'X-Org-Id': str(organization.id),
            'X-Org-Slug': organization.slug,
        }
    else:
        headers = {
            'X-Authenticated-User': None,
            'X-Org-Name': None,
            'X-Org-Id': None,
            'X-Org-Slug': None,
        }
    
    try:
        if request.method == 'GET':
            response = requests.get(flask_url, headers=headers, timeout=5)
        elif request.method == 'POST':
            response = requests.post(
                flask_url,
                headers=headers,
                data=request.body,
                timeout=5
            )
        else:
            response = requests.request(
                request.method,
                flask_url,
                headers=headers,
                data=request.body,
                timeout=5
            )
        
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'text/html')
        )
    
    except requests.RequestException as e:
        return HttpResponse(f"Error connecting: {str(e)}", status=502)