import hashlib
import secrets
from collections import defaultdict
from collections import Counter
from copy import deepcopy
import base64
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, time, timezone as dt_timezone
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import (Workspace, Employee, Event, Shift, Publication, Audit, TimeOff,
                     Availability, AccessToken, Outbox, ShiftRequest, CoverageRequirement)

def workspace(): return Workspace.objects.get_or_create(pk=1)[0]

def guard():
    # SQLite IMMEDIATE transactions acquire the writer lock at BEGIN. The epoch
    # is also a clear serialization row for a later PostgreSQL migration.
    Workspace.objects.filter(pk=1).update(version=F('version') + 1)

def manager(user): return user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser)

def scoped_events(user):
    qs = Event.objects.select_related('location').prefetch_related('shifts__employee', 'shifts__department', 'shifts__skill')
    if user.is_superuser: return qs
    if not manager(user) or not hasattr(user, 'employee'): return qs.none()
    return qs.filter(location__in=user.employee.locations.all(), shifts__department__in=user.employee.departments.all()).distinct()

def scoped_employees(user):
    qs = Employee.objects.select_related('user').prefetch_related('departments', 'locations', 'skills')
    if user.is_superuser: return qs
    if not manager(user) or not hasattr(user, 'employee'): return qs.none()
    return qs.filter(locations__in=user.employee.locations.all(), departments__in=user.employee.departments.all()).distinct()

def can_manage(user, event):
    if not manager(user): return False
    if user.is_superuser: return True
    if not scoped_events(user).filter(pk=event.pk).exists(): return False
    # A manager cannot alter another department's assignments indirectly by
    # publishing or moving a mixed-department Event.
    return not event.shifts.exclude(department__in=user.employee.departments.all()).exists()

def require_manage(user, event):
    if not can_manage(user,event): raise PermissionDenied('This event is outside your management scope.')

def can_edit_employee(user, employee):
    if user.is_superuser: return True
    if not manager(user) or not hasattr(user,'employee') or employee.user.is_staff: return False
    return (scoped_employees(user).filter(pk=employee.pk).exists()
            and not employee.departments.exclude(pk__in=user.employee.departments.values('pk')).exists()
            and not employee.locations.exclude(pk__in=user.employee.locations.values('pk')).exists())

def audit(user, action, target, details=None):
    Audit.objects.create(actor=user,action=action,target=str(target),details=details or {})

def local_datetime(value, zone):
    naive = datetime.fromisoformat(value) if isinstance(value,str) else value
    if naive.tzinfo: return naive
    tz = ZoneInfo(zone)
    aware = naive.replace(tzinfo=tz)
    if aware.astimezone(dt_timezone.utc).astimezone(tz).replace(tzinfo=None) != naive:
        raise ValidationError('That time does not exist because the clocks change. Choose another time.')
    if aware.utcoffset() != naive.replace(tzinfo=tz,fold=1).utcoffset():
        raise ValidationError('That hour occurs twice because the clocks change. Choose an unambiguous time.')
    return aware

def overlap(a,b,c,d): return a < d and c < b

def bounds(event, phase):
    w=workspace();h=timedelta(minutes=w.handover_minutes)
    return {'pre':(event.starts-timedelta(minutes=w.pre_minutes),event.starts+h),
            'during':(event.starts,event.ends+h),'post':(event.ends,event.ends+timedelta(minutes=w.post_minutes))}[phase]

def published_shifts(employee=None, start=None, end=None):
    result=[]
    active_ids=set(Employee.objects.filter(user__is_active=True,ended_at__isnull=True).values_list('pk',flat=True))
    for e in Event.objects.exclude(published_snapshot={}):
        snap=e.published_snapshot
        if snap.get('canceled'): continue
        for original in snap.get('shifts',[]):
            item=dict(original);item['starts']=parse_datetime(item['starts']);item['ends']=parse_datetime(item['ends'])
            if item.get('employee') not in active_ids: item['employee']=None;item['name']='Open shift'
            if employee and item['employee'] != employee.pk: continue
            if start and item['ends'] <= start or end and item['starts'] >= end: continue
            item.update(event_id=e.pk,event_name=snap['name'],location=snap['location'],location_id=snap['location_id'],zone=snap['zone'],revision=e.published_version)
            result.append(item)
    return sorted(result,key=lambda x:(x['starts'],x['id']))

def unavailable(employee, starts, ends):
    zone=ZoneInfo(workspace().timezone)
    first=starts.astimezone(zone).date()-timedelta(days=1)
    last=ends.astimezone(zone).date()
    for q in TimeOff.objects.filter(employee=employee,status='approved'):
        a=datetime.combine(q.first_day,time.min,zone);b=datetime.combine(q.last_day+timedelta(days=1),time.min,zone)
        if overlap(starts,ends,a,b): return 'Approved time off'
    for rule in Availability.objects.filter(employee=employee):
        date=first
        while date<=last:
            if rule.date==date or rule.date is None and rule.weekday==date.weekday():
                a=datetime.combine(date,rule.starts,zone);b=datetime.combine(date,rule.ends,zone)
                if b<=a: b+=timedelta(days=1)
                if overlap(starts,ends,a,b): return 'Outside availability'
            date+=timedelta(days=1)
    return None

def commitments(employee, exclude_shift=None):
    records=[];seen=set()
    for s in Shift.objects.filter(employee=employee,event__canceled=False).select_related('event'):
        if s.pk==exclude_shift: continue
        value=(s.pk,s.starts,s.ends,s.event.location_id);seen.add(value);records.append(value)
    for s in published_shifts(employee):
        if s['id']==exclude_shift: continue
        value=(s['id'],s['starts'],s['ends'],s['location_id'])
        if value not in seen: records.append(value)
    return records

def eligibility(employee, shift, *, check_hours=True):
    if not employee or not employee.active: return ['Account is inactive']
    reasons=[]
    if shift.ends<=shift.starts or shift.ends-shift.starts>timedelta(hours=24): reasons.append('Split this shift into parts of no more than 24 hours')
    if not employee.locations.filter(pk=shift.event.location_id).exists(): reasons.append('Different location')
    if not employee.departments.filter(pk=shift.department_id).exists(): reasons.append('Different department')
    if not employee.skills.filter(pk=shift.skill_id).exists(): reasons.append('Needs '+shift.skill.name)
    off=unavailable(employee,shift.starts,shift.ends)
    if off: reasons.append(off)
    existing=commitments(employee,shift.pk)
    travel=timedelta(minutes=workspace().travel_minutes)
    for _,a,b,loc in existing:
        if overlap(shift.starts,shift.ends,a,b): reasons.append('Overlapping shift')
        elif loc!=shift.event.location_id and overlap(shift.starts,shift.ends,a-travel,b+travel): reasons.append('Not enough travel time')
    if check_hours:
        zone=ZoneInfo(workspace().timezone);date=shift.starts.astimezone(zone).date();week=date-timedelta(days=date.weekday())
        while datetime.combine(week,time.min,zone)<shift.ends:
            left=datetime.combine(week,time.min,zone);right=datetime.combine(week+timedelta(days=7),time.min,zone)
            # Deduplicate a slot represented by an unchanged draft and published
            # revision; different revisions reserve conservative availability.
            by_slot=defaultdict(list)
            for sid,a,b,_ in existing+[(shift.pk,shift.starts,shift.ends,shift.event.location_id)]:
                a=max(a,left);b=min(b,right)
                if a<b: by_slot[sid].append((a,b))
            seconds=0
            for intervals in by_slot.values():
                merged=[]
                for a,b in sorted(intervals):
                    if merged and a<=merged[-1][1]: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
                    else: merged.append((a,b))
                seconds+=sum((b.astimezone(dt_timezone.utc)-a.astimezone(dt_timezone.utc)).total_seconds() for a,b in merged)
            if seconds/3600>employee.weekly_limit+0.00001: reasons.append('Weekly hours limit exceeded')
            week+=timedelta(days=7)
    return list(dict.fromkeys(reasons))

def event_issues(event):
    if event.canceled: return []
    issues=[]
    shifts=list(event.shifts.select_related('employee__user','skill','event','department'))
    for s in shifts:
        if s.employee:
            issues.extend(f'{s.employee.name}: {reason}' for reason in eligibility(s.employee,s))
    required=Counter((s.phase,s.department_id,s.skill_id) for s in shifts)
    for r in event.requirements.all(): required[(r.phase,r.department_id,r.skill_id)]=r.minimum
    for key,minimum in required.items():
        phase,department_id,skill_id=key;a,b=bounds(event,phase)
        slots=[s for s in shifts if (s.phase,s.department_id,s.skill_id)==key]
        points=sorted({a,b}|{max(a,min(b,d)) for s in slots for d in (s.starts,s.ends)})
        for left,right in zip(points,points[1:]):
            if left<right and sum(s.starts<=left and s.ends>=right for s in slots)<minimum:
                label=dict(Shift.PHASES)[phase]
                issues.append(f'{label}: coverage is shorter than the rule requires for {slots[0].department.name if slots else "this department"}')
                break
    return list(dict.fromkeys(issues))

@transaction.atomic
def split_shift(shift_id,user,expected,cut):
    guard();s=Shift.objects.select_related('event__location','skill','department').get(pk=shift_id);require_manage(user,s.event)
    if s.event.version!=expected: raise ValidationError('Someone changed this event. Reload before splitting the shift.')
    handover=timedelta(minutes=workspace().handover_minutes)
    if not s.starts<cut<s.ends-handover: raise ValidationError('Choose a handover time inside the shift, leaving room for the handover overlap.')
    if s.event.shifts.count()>=200: raise ValidationError('This event already has 200 shift slots.')
    count=s.event.shifts.filter(phase=s.phase,department=s.department,skill=s.skill).count()
    CoverageRequirement.objects.get_or_create(event=s.event,phase=s.phase,department=s.department,skill=s.skill,defaults={'minimum':count})
    previous_end=s.ends;s.ends=cut+handover
    if s.employee:
        reasons=eligibility(s.employee,s)
        if reasons: raise ValidationError(reasons)
    s.save(update_fields=['ends'])
    new=Shift.objects.create(event=s.event,phase=s.phase,department=s.department,skill=s.skill,starts=cut,ends=previous_end)
    Event.objects.filter(pk=s.event_id).update(version=F('version')+1)
    audit(user,'Split shift with handover',s.pk,{'new_shift':new.pk,'handover_minutes':workspace().handover_minutes})
    return new

def snapshot(event):
    return {'name':event.name,'location':event.location.name,'location_id':event.location_id,'zone':event.location.timezone,
            'starts':event.starts.isoformat(),'ends':event.ends.isoformat(),'canceled':event.canceled,
            'shifts':[{'id':s.pk,'starts':s.starts.isoformat(),'ends':s.ends.isoformat(),'phase':s.phase,
                       'department':s.department.name,'skill':s.skill.name,'employee':s.employee_id,
                       'name':s.employee.name if s.employee_id else 'Open shift'}
                      for s in event.shifts.select_related('employee','department','skill')]}

def cipher():
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()))

def queue(user,key,subject,body,recipient=''):
    if user.is_active:
        Outbox.objects.get_or_create(key=key,defaults={'user':user,'subject':subject,'body':cipher().encrypt(body.encode()).decode(),'recipient':recipient,'available_at':timezone.now()})

def record_publication(event,user,new_snapshot,*,preserve_draft=False):
    old=event.published_snapshot;old_version=event.published_version
    event.published_snapshot=new_snapshot;event.published_version=event.version
    event.save(update_fields=['published_snapshot','published_version'])
    Publication.objects.create(event=event,version=event.version,snapshot=new_snapshot,actor=user)
    audit(user,'Published event',event.pk,{'previous_revision':old_version,'revision':event.version})
    if workspace().updates_enabled:
        before=defaultdict(list);after=defaultdict(list)
        for s in old.get('shifts',[]):
            if s.get('employee'): before[s['employee']].append(s)
        if not new_snapshot.get('canceled'):
            for s in new_snapshot.get('shifts',[]):
                if s.get('employee'): after[s['employee']].append(s)
        for emp_id in before.keys()|after.keys():
            changed=before[emp_id]!=after[emp_id] or any(old.get(k)!=new_snapshot.get(k) for k in ('name','location','canceled'))
            if changed:
                emp=Employee.objects.select_related('user').get(pk=emp_id)
                lines=[f'Your schedule for {new_snapshot["name"]} has changed.']
                if before[emp_id]:
                    lines.append('Previously:')
                    for s in before[emp_id]:
                        zone=old['zone'];a=parse_datetime(s['starts']).astimezone(ZoneInfo(zone));b=parse_datetime(s['ends']).astimezone(ZoneInfo(zone))
                        lines.append(f'{a:%a %b %d, %I:%M %p} – {b:%a %b %d, %I:%M %p} · {old["location"]} · {zone}')
                if after[emp_id]: lines.append('Your published shifts now:')
                for s in after[emp_id]:
                    zone=new_snapshot['zone'];d=parse_datetime(s['starts']).astimezone(ZoneInfo(zone))
                    end=parse_datetime(s['ends']).astimezone(ZoneInfo(zone))
                    lines.append(f'{d:%a %b %d, %I:%M %p} – {end:%a %b %d, %I:%M %p} · {new_snapshot["location"]} · {zone}')
                if not after[emp_id]: lines.append('Your assignment for this event has been canceled or reassigned.')
                lines.append(settings.APP_BASE_URL+'/my/schedule/')
                queue(emp.user,f'event:{event.pk}:{event.version}:{emp_id}','Your schedule has changed','\n\n'.join(lines))
    if preserve_draft:
        # A targeted leave/offboarding publication must not mark unrelated
        # manager draft edits as already published.
        event.version+=1;event.save(update_fields=['version'])

@transaction.atomic
def publish(event_id,user,expected):
    guard();e=Event.objects.select_for_update().select_related('location').get(pk=event_id);require_manage(user,e)
    if e.version!=expected: raise ValidationError('Someone changed this event. Reload and review the latest version.')
    issues=event_issues(e)
    if issues: raise ValidationError(issues)
    if not e.dirty: return e
    record_publication(e,user,snapshot(e));return e

@transaction.atomic
def assign(shift_id,user,expected,employee,starts,ends):
    guard();s=Shift.objects.select_related('event__location','skill','department').get(pk=shift_id);require_manage(user,s.event)
    if s.event.version!=expected: raise ValidationError('Someone changed this event. Reload before saving.')
    if ends<=starts or ends-starts>timedelta(hours=24): raise ValidationError('Choose a shift longer than zero and no longer than 24 hours.')
    s.starts=starts;s.ends=ends;s.employee=employee
    if employee:
        reasons=eligibility(employee,s)
        if reasons: raise ValidationError(reasons)
    s.save();Event.objects.filter(pk=s.event_id).update(version=F('version')+1)
    audit(user,'Updated draft shift',s.pk,{'employee_id':employee.pk if employee else None})

def create_token(user,purpose,days=7,payload=''):
    raw=secrets.token_urlsafe(32)
    AccessToken.objects.create(user=user,purpose=purpose,payload=payload,digest=hashlib.sha256(raw.encode()).hexdigest(),expires_at=timezone.now()+timedelta(days=days))
    return raw

def get_token(raw,purpose):
    if len(raw)>150: return None
    return AccessToken.objects.select_related('user').filter(digest=hashlib.sha256(raw.encode()).hexdigest(),purpose=purpose,
                revoked_at__isnull=True,expires_at__gt=timezone.now(),user__is_active=True).first()

def remove_future_employee(employee,actor):
    now=timezone.now()
    affected=set(Shift.objects.filter(employee=employee,ends__gt=now).values_list('event_id',flat=True))
    Shift.objects.filter(employee=employee,ends__gt=now).update(employee=None)
    for e in Event.objects.select_related('location'):
        was_dirty=e.dirty
        old=deepcopy(e.published_snapshot)
        changed=False
        for s in old.get('shifts',[]):
            if s.get('employee')==employee.pk and parse_datetime(s['ends'])>now:
                s['employee']=None;s['name']='Open shift';changed=True
        if changed or e.pk in affected:
            e.version+=1;e.save(update_fields=['version'])
            if changed: record_publication(e,actor,old,preserve_draft=was_dirty)
    return len(affected)

@transaction.atomic
def terminate(employee_id,actor):
    guard();employee=Employee.objects.select_related('user').get(pk=employee_id)
    if not manager(actor) or not scoped_employees(actor).filter(pk=employee.pk).exists(): raise PermissionDenied
    if employee.user.is_superuser or employee.user_id==actor.pk or employee.user.is_staff and not actor.is_superuser:
        raise ValidationError('An administrator must handle this account. You cannot end your own access.')
    if not actor.is_superuser and (employee.departments.exclude(pk__in=actor.employee.departments.values('pk')).exists() or employee.locations.exclude(pk__in=actor.employee.locations.values('pk')).exists()):
        raise PermissionDenied('An administrator must handle a staff member shared with other departments or locations.')
    if employee.ended_at: return
    employee.ended_at=timezone.now();employee.save(update_fields=['ended_at'])
    employee.user.is_active=False;employee.user.save(update_fields=['is_active'])
    AccessToken.objects.filter(user=employee.user,revoked_at__isnull=True).update(revoked_at=timezone.now())
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        if session.get_decoded().get('_auth_user_id')==str(employee.user_id): session.delete()
    TimeOff.objects.filter(employee=employee,status='pending').update(status='closed')
    ShiftRequest.objects.filter(employee=employee,status='pending').update(status='closed')
    Outbox.objects.filter(user=employee.user,status__in=['pending','sending']).update(status='canceled')
    affected=remove_future_employee(employee,actor)
    audit(actor,'Ended employment',employee.pk,{'reopened_events':affected,'history_retained':True})

@transaction.atomic
def decide_claim(claim_id,actor,approve):
    guard();claim=ShiftRequest.objects.select_related('employee__user','shift__event','shift__skill','shift__department').get(pk=claim_id)
    require_manage(actor,claim.shift.event)
    if claim.status!='pending': raise ValidationError('This request has already been handled.')
    if approve:
        if claim.shift.employee_id: raise ValidationError('This shift has already been filled.')
        reasons=eligibility(claim.employee,claim.shift)
        if reasons: raise ValidationError(reasons)
        claim.shift.employee=claim.employee;claim.shift.save(update_fields=['employee'])
        e=claim.shift.event;e.version+=1;e.save(update_fields=['version'])
        # Approval changes the manager draft; staff sees it after publication.
        ShiftRequest.objects.filter(shift=claim.shift,status='pending').exclude(pk=claim.pk).update(status='closed')
    claim.status='approved' if approve else 'declined';claim.save(update_fields=['status'])
    audit(actor,'Approved shift request' if approve else 'Declined shift request',claim.pk)

@transaction.atomic
def decide_leave(request_id,actor,approve):
    guard();q=TimeOff.objects.select_related('employee__user').get(pk=request_id)
    if not manager(actor) or not scoped_employees(actor).filter(pk=q.employee_id).exists(): raise PermissionDenied
    if q.status!='pending': raise ValidationError('This request has already been handled.')
    q.status='approved' if approve else 'declined';q.save(update_fields=['status'])
    if approve:
        zone=ZoneInfo(workspace().timezone);a=datetime.combine(q.first_day,time.min,zone);b=datetime.combine(q.last_day+timedelta(days=1),time.min,zone)
        event_ids=set(Shift.objects.filter(employee=q.employee,starts__lt=b,ends__gt=a).values_list('event_id',flat=True))
        Shift.objects.filter(employee=q.employee,starts__lt=b,ends__gt=a).update(employee=None)
        for e in Event.objects.select_related('location'):
            was_dirty=e.dirty
            snap=deepcopy(e.published_snapshot);changed=False
            for s in snap.get('shifts',[]):
                if s.get('employee')==q.employee_id and overlap(parse_datetime(s['starts']),parse_datetime(s['ends']),a,b):
                    s['employee']=None;s['name']='Open shift';changed=True
            if changed or e.pk in event_ids:
                e.version+=1;e.save(update_fields=['version'])
                if changed: record_publication(e,actor,snap,preserve_draft=was_dirty)
    queue(q.employee.user,f'leave:{q.pk}:{q.status}','Your time-off request',f'Your time-off request for {q.first_day} through {q.last_day} was {q.status}.\n\n{settings.APP_BASE_URL}/my/time-off/')
    audit(actor,'Time off '+q.status,q.pk)
