import requests
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

FLASK_APP_URL = 'http://app-plus:8001'
BASE_URL = '/partners/dashboard'

@login_required
def flask_proxy(request):
    """
    Forwards requests to Flask app with user headers and other metadata
    """
    # Get the authenticated user
    user = request.user
    path = request.get_full_path().replace(BASE_URL, '', 1)
    
    flask_url = f"{FLASK_APP_URL}{path}"
    
    headers = {
        'X-Authenticated-User': user.username,
        'X-User-Email': user.email,
        'X-User-ID': str(user.id),
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
        
        # Return flask's response
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'text/html')
        )
    
    except requests.RequestException as e:
        return HttpResponse(f"Error connecting: {str(e)}", status=502)