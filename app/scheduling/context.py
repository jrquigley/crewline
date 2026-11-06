from .models import Workspace, TimeOff, ShiftRequest
from django.conf import settings

def navigation(request):
    if not request.user.is_authenticated:
        return {'is_manager': False}
    from .services import scoped_employees
    manager = request.user.is_staff or request.user.is_superuser
    count = 0
    if manager:
        ids = scoped_employees(request.user).values_list('id', flat=True)
        count = TimeOff.objects.filter(employee_id__in=ids,status='pending').count() + ShiftRequest.objects.filter(employee_id__in=ids,status='pending').count()
    return {'is_manager': manager, 'workspace': Workspace.objects.first(), 'request_count': count,
            'smtp_ready': settings.SMTP_CONFIGURED, 'site_origin': settings.APP_BASE_URL,
            'display_name': getattr(getattr(request.user,'employee',None),'name','') or request.user.first_name or 'My account'}
