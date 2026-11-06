from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction, close_old_connections
from django.utils import timezone
from .models import Outbox, Employee, LoginAttempt
from . import services as svc

def create_digests(now=None):
    now=now or timezone.now();w=svc.workspace();local=now.astimezone(ZoneInfo(w.timezone))
    if not w.digest_enabled or local.weekday()!=w.digest_day or local.time().replace(tzinfo=None)<w.digest_time: return 0
    monday=local.date()+timedelta(days=7-local.weekday());start=datetime.combine(monday,time.min,ZoneInfo(w.timezone));end=datetime.combine(monday+timedelta(days=7),time.min,ZoneInfo(w.timezone))
    count=0
    for employee in Employee.objects.filter(ended_at__isnull=True,user__is_active=True).select_related('user'):
        key=f'digest:{employee.pk}:{monday}'
        if Outbox.objects.filter(key=key).exists(): continue
        shifts=svc.published_shifts(employee,start,end);lines=[f'Your schedule for the week of {monday:%B %d}.']
        for s in shifts:
            z=ZoneInfo(s['zone']);a=s['starts'].astimezone(z);b=s['ends'].astimezone(z)
            lines.append(f'{a:%a %b %d, %I:%M %p} – {b:%I:%M %p}: {s["event_name"]} · {s["location"]} · {s["zone"]}')
        if not shifts: lines.append('You have no published shifts for this week yet.')
        lines.append(settings.APP_BASE_URL+'/my/schedule/')
        svc.queue(employee.user,key,'Your upcoming weekly schedule','\n\n'.join(lines));count+=1
    return count

def deliver_one():
    if not settings.SMTP_CONFIGURED: return False
    now=timezone.now()
    with transaction.atomic():
        svc.guard()
        # A crash after SMTP acceptance is ambiguous. Surface it for review
        # rather than silently sending the same email a second time.
        Outbox.objects.filter(status='sending',claimed_at__lt=now-timedelta(minutes=5)).update(status='review',error='Delivery outcome needs review')
        job=Outbox.objects.filter(status='pending',available_at__lte=now).select_related('user').order_by('pk').first()
        if not job: return False
        recipient=job.recipient or job.user.email
        if not job.user.is_active:
            job.status='canceled';job.save(update_fields=['status']);return True
        if recipient.lower().endswith(('.example','@example.com')):
            job.status='blocked';job.error='Fictional recipient is not emailed';job.save(update_fields=['status','error']);return True
        job.status='sending';job.attempts+=1;job.claimed_at=now;job.save(update_fields=['status','attempts','claimed_at'])
    try:
        if not job.user.__class__.objects.filter(pk=job.user_id,is_active=True).exists():
            Outbox.objects.filter(pk=job.pk,status='sending').update(status='canceled');return True
        body=svc.cipher().decrypt(job.body.encode()).decode()
        sent=send_mail(job.subject,body,settings.DEFAULT_FROM_EMAIL,[recipient],fail_silently=False)
        if sent!=1: raise RuntimeError('Mail provider did not confirm delivery')
        Outbox.objects.filter(pk=job.pk,status='sending').update(status='sent',sent_at=timezone.now(),error='')
    except Exception:
        # Avoid logging message bodies, email addresses or private access URLs.
        Outbox.objects.filter(pk=job.pk,status='sending').update(status='review',error='Provider failure; review before retry')
    return True

def tick():
    close_old_connections()
    create_digests()
    for _ in range(20):
        if not deliver_one(): break
    LoginAttempt.objects.filter(updated_at__lt=timezone.now()-timedelta(days=2)).delete()
    close_old_connections()
