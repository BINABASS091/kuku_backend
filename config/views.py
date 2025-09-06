from django.http import JsonResponse
from django.views import View

class APIRootView(View):
    """
    API Root View that provides information about available API endpoints.
    """
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'name': 'Smart Kuku API',
            'version': '1.0.0',
            'description': 'Smart Kuku Poultry Management System API',
            'endpoints': {
                'api_documentation': '/api/schema/swagger-ui/',
                'api_schema': '/api/schema/',
                'authentication': {
                    'obtain_token': '/api/token/',
                    'refresh_token': '/api/token/refresh/'
                },
                'api_v1': '/api/v1/'
            }
        })
