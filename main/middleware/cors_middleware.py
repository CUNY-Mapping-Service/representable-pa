class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        allowed_origins = [
            'http://localhost:8000',
            'http://localhost:8888',
            
            'http://127.0.0.1:8000',
            'http://127.0.0.1:8888'
        ]

        # Set CORS headers
        if request.method == 'OPTIONS':
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Max-Age"] = "86400"
            return response

        origin = request.META.get('HTTP_ORIGIN')
        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin

        return response
