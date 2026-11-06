from datetime import datetime, timezone as utc, timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from . import services as svc
from .models import Publication

def escape(value):
    return str(value).replace('\\','\\\\').replace('\r','').replace('\n','\\n').replace(';','\\;').replace(',','\\,')

def fold(line):
    output=[];part='';size=0
    for char in line:
        count=len(char.encode('utf-8'))
        if size+count>74: output.append(part);part=' '+char;size=1+count
        else: part+=char;size+=count
    output.append(part);return '\r\n'.join(output)

def stamp(value): return value.astimezone(utc.utc).strftime('%Y%m%dT%H%M%SZ')

def calendar_feed(request,token):
    grant=svc.get_token(token,'calendar')
    if not grant or not hasattr(grant.user,'employee') or not grant.user.employee.active:
        return HttpResponse('Calendar subscription is unavailable.',status=401,content_type='text/plain')
    employee=grant.user.employee
    now=timezone.now();left=now-timedelta(days=90);right=now+timedelta(days=365)
    current={s['id']:s for s in svc.published_shifts(employee,left,right)}
    known={}
    for pub in Publication.objects.select_related('event').order_by('created_at','pk'):
        for s in pub.snapshot.get('shifts',[]):
            if s.get('employee')==employee.pk and left<parse_datetime(s['ends']) and parse_datetime(s['starts'])<right:
                known[s['id']]={**s,'event_name':pub.snapshot['name'],'location':pub.snapshot['location'],'revision':pub.event.published_version,
                                'starts':parse_datetime(s['starts']),'ends':parse_datetime(s['ends'])}
    known.update(current)
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Crewline//Staff schedule//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Crewline shifts']
    for shift_id,s in sorted(known.items()):
        lines+=['BEGIN:VEVENT',f'UID:shift-{shift_id}@crewline.local',f'SEQUENCE:{s["revision"]}',f'DTSTAMP:{stamp(now)}',
                f'DTSTART:{stamp(s["starts"])}',f'DTEND:{stamp(s["ends"])}',
                'SUMMARY:'+escape(s['event_name']),'LOCATION:'+escape(s['location']),
                'STATUS:'+('CONFIRMED' if shift_id in current else 'CANCELLED'),'END:VEVENT']
    lines.append('END:VCALENDAR')
    response=HttpResponse('\r\n'.join(fold(x) for x in lines)+'\r\n',content_type='text/calendar; charset=utf-8')
    response['Content-Disposition']='inline; filename="crewline.ics"'
    return response
