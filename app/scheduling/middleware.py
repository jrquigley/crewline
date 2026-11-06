from django.contrib.auth import logout
from django.shortcuts import redirect

class AccessMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.ended_at:
            logout(request)
            return redirect('login')
        response = self.get_response(request)
        if not request.path.startswith('/static/'):
            response['Cache-Control'] = 'no-store, private'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response
