import csv
import hashlib
from copy import deepcopy
from datetime import datetime, timedelta, time
from functools import wraps
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import F
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods
from .models import *
from .forms import *
from . import services as svc

def manager_required(fn):
    @login_required
    @wraps(fn)
    def inner(request,*args,**kwargs):
        if not svc.manager(request.user): raise PermissionDenied
        return fn(request,*args,**kwargs)
    return inner

def staff_profile(request):
    employee=getattr(request.user,'employee',None)
    if not employee or not employee.active: raise PermissionDenied('Your account has no active staff profile.')
    return employee

def fail(request,error):
    for message in error.messages if hasattr(error,'messages') else [str(error)]: messages.error(request,message)

def local_input(value,zone): return value.astimezone(ZoneInfo(zone)).strftime('%Y-%m-%dT%H:%M')

def present(items):
    for s in items:
        zone=ZoneInfo(s['zone']);a=s['starts'].astimezone(zone);b=s['ends'].astimezone(zone)
        s.update(day=a.strftime('%a'),day_number=a.day,date_label=a.strftime('%A, %B %d').replace(' 0',' '),
                 time_label=a.strftime('%I:%M%p').lstrip('0').lower()+' – '+b.strftime('%I:%M%p').lstrip('0').lower()+(b.strftime(' · %a') if b.date()!=a.date() else ''),
                 hours=round((s['ends']-s['starts']).total_seconds()/3600,2))
    return items

def home(request):
    if not request.user.is_authenticated: return redirect('login')
    return redirect('dashboard' if svc.manager(request.user) else 'staff_home')

def attempt_keys(request,username):
    ip=request.META.get('REMOTE_ADDR','unknown')
    return [(hashlib.sha256(('account:'+username.lower()).encode()).hexdigest(),5),
            (hashlib.sha256(('address:'+ip).encode()).hexdigest(),40)]

def blocked(keys): return LoginAttempt.objects.filter(key__in=[k for k,_ in keys],blocked_until__gt=timezone.now()).exists()

@transaction.atomic
def failed_attempt(keys):
    now=timezone.now()
    for key,limit in keys:
        row,_=LoginAttempt.objects.get_or_create(key=key)
        if row.updated_at<now-timedelta(minutes=15): row.failures=0
        row.failures+=1
        if row.failures>=limit: row.blocked_until=now+timedelta(minutes=15)
        row.save()

@require_http_methods(['GET','POST'])
def sign_in(request):
    if request.user.is_authenticated: return redirect('home')
    form=SignInForm(request,data=request.POST or None)
    status=200
    if request.method=='POST':
        keys=attempt_keys(request,request.POST.get('username','')[:254])
        if blocked(keys): return render(request,'registration/login.html',{'form':SignInForm(request),'locked':True},status=429)
        elif form.is_valid():
            login(request,form.get_user())
            LoginAttempt.objects.filter(key=keys[0][0]).delete()
            target=request.GET.get('next','/')
            if not url_has_allowed_host_and_scheme(target,{request.get_host()},require_https=not settings.LOCAL_HTTP): target='/'
            return redirect(target)
        else: failed_attempt(keys)
    return render(request,'registration/login.html',{'form':form},status=status)

@login_required
@require_POST
def sign_out(request): logout(request);return redirect('login')

@require_http_methods(['GET','POST'])
def reset_request(request):
    form=ResetRequestForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        keys=attempt_keys(request,'reset:'+request.META.get('REMOTE_ADDR','unknown'))
        if not blocked(keys):
            failed_attempt(keys)
            user=User.objects.filter(username__iexact=form.cleaned_data['email'],is_active=True).first()
            if user and settings.SMTP_CONFIGURED:
                token=svc.create_token(user,'password',days=1/24)
                svc.queue(user,'reset:'+hashlib.sha256(token.encode()).hexdigest(),'Reset your Crewline password',
                          settings.APP_BASE_URL+'/access/'+token+'/')
        return render(request,'registration/reset_sent.html')
    return render(request,'registration/reset.html',{'form':form})

@require_http_methods(['GET','POST'])
def access_link(request,token):
    grant=svc.get_token(token,'invite') or svc.get_token(token,'password')
    if not grant: return render(request,'registration/expired.html',status=400)
    form=SetPasswordForm(grant.user,request.POST or None,label_suffix='')
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            svc.guard()
            current=svc.get_token(token,grant.purpose)
            if not current: return render(request,'registration/expired.html',status=400)
            form.save()
            AccessToken.objects.filter(user=grant.user,purpose__in=['invite','password'],revoked_at__isnull=True).update(revoked_at=timezone.now())
            svc.audit(grant.user,'Set account password',grant.user_id)
        messages.success(request,'Your password is set. Sign in with your email address.')
        return redirect('login')
    return render(request,'registration/access.html',{'form':form,'account_email':grant.user.email})

@require_http_methods(['GET','POST'])
def confirm_email(request,token):
    grant=svc.get_token(token,'email')
    if not grant: return render(request,'registration/expired.html',status=400)
    if request.method=='POST':
        with transaction.atomic():
            svc.guard();grant=svc.get_token(token,'email')
            if not grant: return render(request,'registration/expired.html',status=400)
            if User.objects.filter(username__iexact=grant.payload).exclude(pk=grant.user_id).exists():
                messages.error(request,'That address is already in use. Contact your manager.');return redirect('login')
            grant.user.username=grant.payload;grant.user.email=grant.payload;grant.user.save(update_fields=['username','email'])
            Employee.objects.filter(user=grant.user).update(pending_email='')
            AccessToken.objects.filter(user=grant.user,purpose__in=['email','invite','password'],revoked_at__isnull=True).update(revoked_at=timezone.now())
            svc.audit(grant.user,'Verified contact email',grant.user_id)
        messages.success(request,'Email address verified. Use the new address to sign in.')
        return redirect('login')
    return render(request,'registration/confirm_email.html',{'new_email':grant.payload})

@manager_required
def dashboard(request):
    today=timezone.localdate();week=today-timedelta(days=today.weekday())
    try: first=datetime.fromisoformat(request.GET.get('week','')).date() if request.GET.get('week') else today
    except ValueError: first=today
    last=first+timedelta(days=30)
    events=svc.scoped_events(request.user).filter(ends__gte=datetime.combine(first,time.min,ZoneInfo(svc.workspace().timezone)),starts__lt=datetime.combine(last,time.min,ZoneInfo(svc.workspace().timezone)))
    location=request.GET.get('location','');dept=request.GET.get('department','');query=request.GET.get('q','')[:100]
    if location.isdigit(): events=events.filter(location_id=location)
    if dept.isdigit(): events=events.filter(shifts__department_id=dept).distinct()
    if query: events=events.filter(name__icontains=query)
    if request.GET.get('open')=='1': events=events.filter(shifts__employee__isnull=True).distinct()
    rows=[];opens=0;dirty=0
    for e in events[:100]:
        e.slots=list(e.shifts.all());e.total=len(e.slots);e.filled=sum(bool(s.employee_id) for s in e.slots);e.open_count=e.total-e.filled
        e.local_start=e.starts.astimezone(ZoneInfo(e.location.timezone));e.local_end=e.ends.astimezone(ZoneInfo(e.location.timezone))
        e.departments=', '.join(dict.fromkeys(s.department.name for s in e.slots));rows.append(e);opens+=e.open_count;dirty+=e.dirty
        e.phase_counts=[{'label':label,'filled':sum(bool(s.employee_id) for s in e.slots if s.phase==phase),'total':sum(s.phase==phase for s in e.slots)} for phase,label in [('pre','Setup'),('during','Event'),('post','Close')]]
    zone=ZoneInfo(svc.workspace().timezone);left=datetime.combine(week,time.min,zone);right=datetime.combine(week+timedelta(days=7),time.min,zone)
    people=[]
    for emp in svc.scoped_employees(request.user).filter(user__is_active=True,ended_at__isnull=True).order_by('name'):
        total=sum((min(s.ends,right)-max(s.starts,left)).total_seconds()/3600 for s in Shift.objects.filter(employee=emp,starts__lt=right,ends__gt=left,event__canceled=False))
        emp.hours=round(total,2);emp.bar=min(100,round(total/emp.weekly_limit*100));people.append(emp)
    locations=Location.objects.all() if request.user.is_superuser else request.user.employee.locations.all()
    departments=Department.objects.all() if request.user.is_superuser else request.user.employee.departments.all()
    return render(request,'scheduling/dashboard.html',{'events':rows,'people':people,'open_count':opens,'draft_count':dirty,'locations':locations,'departments':departments,'selected_location':location,'selected_department':dept,'query':query,'week':week,'today':today,'calendar_view':request.GET.get('view')=='week'})

@manager_required
@require_http_methods(['GET','POST'])
def event_create(request):
    initial={'starts':(timezone.localtime()+timedelta(days=1)).strftime('%Y-%m-%dT18:00'),'ends':(timezone.localtime()+timedelta(days=1)).strftime('%Y-%m-%dT21:00')}
    form=EventForm(request.POST or None,initial=initial,user=request.user)
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data
        with transaction.atomic():
            svc.guard();e=Event.objects.create(name=d['name'],location=d['location'],starts=d['starts'],ends=d['ends'],notes=d['notes'],external_context=d['external_context'],created_by=request.user)
            for phase in ('pre','during','post'):
                a,b=svc.bounds(e,phase);Shift.objects.create(event=e,phase=phase,department=d['department'],skill=d['skill'],starts=a,ends=b)
                CoverageRequirement.objects.create(event=e,phase=phase,department=d['department'],skill=d['skill'],minimum=1)
            svc.audit(request.user,'Created event',e.pk)
        messages.success(request,'Event created. Now choose the people for each shift.');return redirect('event_detail',pk=e.pk)
    return render(request,'scheduling/event_form.html',{'form':form,'heading':'Create an event','editing':False})

@manager_required
@require_http_methods(['GET','POST'])
def event_edit(request,pk):
    e=get_object_or_404(svc.scoped_events(request.user),pk=pk);svc.require_manage(request.user,e)
    form=EventForm(request.POST or None,user=request.user,editing=True,initial={'name':e.name,'location':e.location,'starts':local_input(e.starts,e.location.timezone),'ends':local_input(e.ends,e.location.timezone),'notes':e.notes,'external_context':e.external_context,'version':e.version})
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                svc.guard();e.refresh_from_db()
                if e.version!=form.cleaned_data['version']: raise ValidationError('Someone changed this event. Reload before saving.')
                d=form.cleaned_data;start_delta=d['starts']-e.starts;end_delta=d['ends']-e.ends
                e.name=d['name'];e.location=d['location'];e.starts=d['starts'];e.ends=d['ends'];e.notes=d['notes'];e.external_context=d['external_context'];e.version+=1;e.save()
                for s in e.shifts.all():
                    s.starts+=end_delta if s.phase=='post' else start_delta
                    s.ends+=start_delta if s.phase=='pre' else end_delta
                    if s.ends<=s.starts: raise ValidationError('The new event times would invert a custom shift. Adjust that shift before moving the event.')
                    s.save(update_fields=['starts','ends'])
                svc.audit(request.user,'Edited event draft',e.pk)
            messages.success(request,'Draft saved. Publish the event when you are ready to notify staff.');return redirect('event_detail',pk=e.pk)
        except ValidationError as error: form.add_error(None,error)
    return render(request,'scheduling/event_form.html',{'form':form,'heading':'Edit event','editing':True,'event':e})

@manager_required
def event_detail(request,pk):
    e=get_object_or_404(svc.scoped_events(request.user),pk=pk);e.local_start=e.starts.astimezone(ZoneInfo(e.location.timezone));e.local_end=e.ends.astimezone(ZoneInfo(e.location.timezone))
    shifts=list(e.shifts.select_related('employee__user','department','skill'))
    for s in shifts:
        s.local_start=s.starts.astimezone(ZoneInfo(e.location.timezone));s.local_end=s.ends.astimezone(ZoneInfo(e.location.timezone))
        s.problems=svc.eligibility(s.employee,s) if s.employee else []
    return render(request,'scheduling/event_detail.html',{'event':e,'shifts':shifts,'open_count':sum(not s.employee_id for s in shifts),'issues':svc.event_issues(e),'can_edit':svc.can_manage(request.user,e),'coverage_form':CoverageForm(user=request.user,initial={'version':e.version})})

@manager_required
@require_http_methods(['GET','POST'])
def shift_edit(request,pk):
    s=get_object_or_404(Shift.objects.select_related('event__location','skill','department'),pk=pk,event__in=svc.scoped_events(request.user));svc.require_manage(request.user,s.event)
    form=ShiftForm(request.POST or None,user=request.user,shift=s,initial={'employee':s.employee,'starts':local_input(s.starts,s.event.location.timezone),'ends':local_input(s.ends,s.event.location.timezone),'version':s.event.version})
    if request.method=='POST' and form.is_valid():
        try:
            d=form.cleaned_data;svc.assign(s.pk,request.user,d['version'],d['employee'],d['starts'],d['ends'])
            messages.success(request,'Assignment saved to the draft. Publish to update staff schedules.');return redirect('event_detail',pk=s.event_id)
        except ValidationError as error: form.add_error(None,error)
    return render(request,'scheduling/shift_form.html',{'form':form,'shift':s})

@manager_required
@require_POST
def add_coverage(request,pk):
    e=get_object_or_404(svc.scoped_events(request.user),pk=pk);svc.require_manage(request.user,e);form=CoverageForm(request.POST,user=request.user)
    if form.is_valid():
        with transaction.atomic():
            svc.guard();e.refresh_from_db()
            if e.version!=form.cleaned_data['version']: messages.error(request,'This event changed. Reload before adding coverage.');return redirect('event_detail',pk=pk)
            d=form.cleaned_data;a,b=svc.bounds(e,d['phase'])
            if e.shifts.count()+d['count']>200: messages.error(request,'An event supports at most 200 shift slots.');return redirect('event_detail',pk=pk)
            current=e.shifts.filter(phase=d['phase'],department=d['department'],skill=d['skill']).count()
            requirement,_=CoverageRequirement.objects.get_or_create(event=e,phase=d['phase'],department=d['department'],skill=d['skill'],defaults={'minimum':current})
            requirement.minimum+=d['count'];requirement.save(update_fields=['minimum'])
            for _ in range(d['count']): Shift.objects.create(event=e,phase=d['phase'],department=d['department'],skill=d['skill'],starts=a,ends=b)
            e.version+=1;e.save(update_fields=['version']);svc.audit(request.user,'Added event coverage',e.pk,{'count':d['count']})
        messages.success(request,'Coverage added. Choose people for the new shifts.')
    else:
        for error in form.errors.values(): messages.error(request,str(error.as_text()))
    return redirect('event_detail',pk=pk)

@manager_required
@require_http_methods(['GET','POST'])
def shift_split(request,pk):
    s=get_object_or_404(Shift.objects.select_related('event__location','department','skill'),pk=pk,event__in=svc.scoped_events(request.user));svc.require_manage(request.user,s.event)
    midpoint=s.starts+(s.ends-s.starts)/2
    if request.method=='POST':
        try:
            cut=svc.local_datetime(request.POST.get('handover',''),s.event.location.timezone)
            svc.split_shift(s.pk,request.user,int(request.POST.get('version','0')),cut)
            messages.success(request,'Shift split. Choose another person for the second part, then publish the event.');return redirect('event_detail',pk=s.event_id)
        except (ValidationError,ValueError) as error: fail(request,error)
    return render(request,'scheduling/split.html',{'shift':s,'midpoint':local_input(midpoint,s.event.location.timezone)})

@manager_required
@require_http_methods(['GET','POST'])
def event_publish(request,pk):
    e=get_object_or_404(svc.scoped_events(request.user),pk=pk);svc.require_manage(request.user,e)
    if request.method=='POST':
        try:
            expected=int(request.POST.get('version','0'));svc.publish(e.pk,request.user,expected)
            messages.success(request,'Published. Staff can now see this schedule.'+(' Email updates are queued.' if settings.SMTP_CONFIGURED else ' Email will send after SMTP is configured.'))
            return redirect('event_detail',pk=pk)
        except (ValidationError,ValueError) as error: fail(request,error)
    return render(request,'scheduling/publish.html',{'event':e,'issues':svc.event_issues(e),'open_count':e.shifts.filter(employee__isnull=True).count(),'shifts':e.shifts.select_related('employee','department','skill')})

@manager_required
@require_POST
def event_cancel(request,pk):
    e=get_object_or_404(svc.scoped_events(request.user),pk=pk);svc.require_manage(request.user,e)
    with transaction.atomic():
        svc.guard();e.refresh_from_db()
        if str(e.version)!=request.POST.get('version'): messages.error(request,'This event changed. Reload before canceling.');return redirect('event_detail',pk=pk)
        e.canceled=True;e.version+=1;e.save(update_fields=['canceled','version']);svc.publish(e.pk,request.user,e.version)
    messages.success(request,'Event canceled. Its history is retained.');return redirect('dashboard')

@manager_required
def directory(request):
    people=svc.scoped_employees(request.user).order_by('name')
    if request.GET.get('archived')!='1': people=people.filter(ended_at__isnull=True)
    return render(request,'scheduling/directory.html',{'people':people,'archived':request.GET.get('archived')=='1'})

@manager_required
@require_http_methods(['GET','POST'])
def employee_edit(request,pk=None):
    emp=get_object_or_404(svc.scoped_employees(request.user),pk=pk) if pk else None
    if emp and not svc.can_edit_employee(request.user,emp): raise PermissionDenied('An administrator must edit staff shared outside your management scope.')
    form=EmployeeForm(request.POST or None,instance=emp,user=request.user)
    if emp: form.fields['email'].disabled=True
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            svc.guard();record=form.save(commit=False)
            if not emp:
                user=User.objects.create_user(username=form.cleaned_data['email'],email=form.cleaned_data['email']);user.set_unusable_password();user.save()
                record.user=user
            if request.user.is_superuser: record.user.is_staff=form.cleaned_data.get('manage_schedules',False);record.user.save(update_fields=['is_staff'])
            record.save();form.save_m2m();svc.audit(request.user,'Updated staff profile' if emp else 'Created staff profile',record.pk)
        messages.success(request,'Staff details saved.' if emp else 'Staff added. Create their secure sign-in link when you are ready.');return redirect('employee_detail',pk=record.pk)
    return render(request,'scheduling/employee_form.html',{'form':form,'employee':emp})

@manager_required
def employee_detail(request,pk):
    emp=get_object_or_404(svc.scoped_employees(request.user),pk=pk)
    history=Publication.objects.filter(event__in=svc.scoped_events(request.user),snapshot__shifts__isnull=False).order_by('-created_at')[:100]
    retained=[]
    for pub in history:
        for shift in pub.snapshot.get('shifts',[]):
            if shift.get('employee')==emp.pk:
                retained.append({'event':pub.snapshot['name'],'when':pub.created_at,'revision':pub.version})
                break
    invite=request.session.pop('created_invite',None)
    if invite:
        try: invite=svc.cipher().decrypt(invite.encode()).decode()
        except Exception: invite=None
    return render(request,'scheduling/employee_detail.html',{'employee':emp,'assignments':Shift.objects.filter(employee=emp,event__in=svc.scoped_events(request.user)).select_related('event__location'),
                  'history':retained[:12],'can_edit_employee':svc.can_edit_employee(request.user,emp),'invite_url':invite if invite and request.session.pop('invite_employee',None)==emp.pk else None})

@manager_required
@require_POST
def employee_invite(request,pk):
    emp=get_object_or_404(svc.scoped_employees(request.user),pk=pk,ended_at__isnull=True,user__is_active=True)
    if emp.user.is_staff and not request.user.is_superuser: raise PermissionDenied
    with transaction.atomic():
        svc.guard();AccessToken.objects.filter(user=emp.user,purpose='invite',revoked_at__isnull=True).update(revoked_at=timezone.now())
        token=svc.create_token(emp.user,'invite');url=settings.APP_BASE_URL+'/access/'+token+'/'
        svc.queue(emp.user,'invite:'+hashlib.sha256(token.encode()).hexdigest(),'Your Crewline sign-in link',f'Create your password using this one-time link. It expires in seven days.\n\n{url}')
        svc.audit(request.user,'Created sign-in invitation',emp.pk)
    request.session['created_invite']=svc.cipher().encrypt(url.encode()).decode();request.session['invite_employee']=emp.pk
    messages.success(request,'Secure link created. Share it privately with this employee.');return redirect('employee_detail',pk=pk)

@manager_required
@require_http_methods(['GET','POST'])
def employee_terminate(request,pk):
    emp=get_object_or_404(svc.scoped_employees(request.user),pk=pk)
    if request.method=='POST':
        try: svc.terminate(emp.pk,request.user);messages.success(request,'Access ended. Future shifts reopened and historical records retained.');return redirect('employee_detail',pk=pk)
        except ValidationError as error: fail(request,error)
    return render(request,'scheduling/terminate.html',{'employee':emp,'affected':Shift.objects.filter(employee=emp,ends__gt=timezone.now()).count()})

@manager_required
def requests_page(request):
    employees=svc.scoped_employees(request.user)
    leave=TimeOff.objects.filter(employee__in=employees).select_related('employee').order_by('status','first_day')[:100]
    for q in leave:
        zone=ZoneInfo(svc.workspace().timezone);a=datetime.combine(q.first_day,time.min,zone);b=datetime.combine(q.last_day+timedelta(days=1),time.min,zone)
        q.affected=Shift.objects.filter(employee=q.employee,starts__lt=b,ends__gt=a).count()
    claims=ShiftRequest.objects.filter(employee__in=employees,shift__event__in=svc.scoped_events(request.user)).select_related('employee','shift__event').order_by('-created_at')[:100]
    return render(request,'scheduling/requests.html',{'leave':leave,'claims':claims})

@manager_required
@require_POST
def request_decision(request,kind,pk):
    approve=request.POST.get('decision')=='approve'
    try:
        if kind=='leave': svc.decide_leave(pk,request.user,approve)
        elif kind=='shift': svc.decide_claim(pk,request.user,approve)
        else: raise Http404
        messages.success(request,'Request approved.' if approve else 'Request declined.')
    except (TimeOff.DoesNotExist,ShiftRequest.DoesNotExist): raise Http404
    except ValidationError as error: fail(request,error)
    return redirect('requests')

@manager_required
@require_http_methods(['GET','POST'])
def settings_page(request):
    if not request.user.is_superuser: raise PermissionDenied
    w=svc.workspace();form=WorkspaceForm(request.POST or None,instance=w)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic(): svc.guard();form.save();svc.audit(request.user,'Changed workspace settings',w.pk)
        messages.success(request,'Settings saved. Published shift times remain unchanged until you edit and publish an event.');return redirect('settings')
    return render(request,'scheduling/settings.html',{'form':form,'locations':Location.objects.all(),'departments':Department.objects.all(),'skills':Skill.objects.all()})

@manager_required
@require_POST
def catalog_add(request,kind):
    if not request.user.is_superuser: raise PermissionDenied
    name=request.POST.get('name','').strip()[:80]
    model={'department':Department,'location':Location,'skill':Skill}.get(kind)
    if not model or not name: messages.error(request,'Enter a name.');return redirect('settings')
    defaults={'timezone':svc.workspace().timezone} if model==Location else {}
    with transaction.atomic(): svc.guard();obj,created=model.objects.get_or_create(name=name,defaults=defaults);svc.audit(request.user,'Added '+kind,obj.pk)
    messages.success(request,'Added '+name+'.' if created else 'That name already exists.');return redirect('settings')

@manager_required
def hours_page(request):
    today=timezone.localdate();week=today-timedelta(days=today.weekday())
    try: week=datetime.fromisoformat(request.GET['week']).date() if 'week' in request.GET else week
    except ValueError: pass
    week-=timedelta(days=week.weekday());zone=ZoneInfo(svc.workspace().timezone);a=datetime.combine(week,time.min,zone);b=datetime.combine(week+timedelta(days=7),time.min,zone)
    rows=[]
    for emp in svc.scoped_employees(request.user).filter(ended_at__isnull=True).order_by('name'):
        shifts=list(Shift.objects.filter(employee=emp,starts__lt=b,ends__gt=a,event__canceled=False).select_related('event__location'))
        total=round(sum((min(s.ends,b)-max(s.starts,a)).total_seconds()/3600 for s in shifts),2)
        published=round(sum((min(s['ends'],b)-max(s['starts'],a)).total_seconds()/3600 for s in svc.published_shifts(emp,a,b)),2)
        rows.append({'employee':emp,'hours':total,'published':published,'count':len(shifts)})
    if request.GET.get('format')=='csv':
        response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="scheduled-hours.csv"'
        out=csv.writer(response);out.writerow(['Employee','Week starting','Draft hours','Published hours','Weekly limit'])
        for row in rows:
            name=row['employee'].name;name="'"+name if name.startswith(('=','+','-','@','\t','\r')) else name
            out.writerow([name,str(week),row['hours'],row['published'],row['employee'].weekly_limit])
        return response
    return render(request,'scheduling/hours.html',{'rows':rows,'week':week,'previous':week-timedelta(days=7),'next':week+timedelta(days=7)})

@manager_required
def audit_page(request):
    if not request.user.is_superuser: raise PermissionDenied
    return render(request,'scheduling/audit.html',{'entries':Audit.objects.select_related('actor')[:100],'delivery':Outbox.objects.order_by('-pk')[:30]})

@manager_required
@require_POST
def retry_email(request,pk):
    if not request.user.is_superuser: raise PermissionDenied
    with transaction.atomic():
        svc.guard();job=get_object_or_404(Outbox,pk=pk,status='review')
        if not job.user.is_active: job.status='canceled'
        else: job.status='pending';job.available_at=timezone.now();job.error=''
        job.save(update_fields=['status','available_at','error']);svc.audit(request.user,'Manually retried reviewed email',job.pk)
    messages.success(request,'Message returned to the delivery queue.');return redirect('audit')

@login_required
def staff_home(request):
    emp=staff_profile(request);items=present(svc.published_shifts(emp,start=timezone.now()))
    return render(request,'scheduling/staff_home.html',{'employee':emp,'next_shift':items[0] if items else None,'upcoming':items[1:4]})

@login_required
def staff_schedule(request):
    emp=staff_profile(request);items=present(svc.published_shifts(emp,start=timezone.now()-timedelta(days=1),end=timezone.now()+timedelta(days=90)))
    return render(request,'scheduling/staff_schedule.html',{'items':items})

@login_required
def staff_shift(request,pk):
    emp=staff_profile(request);item=next((s for s in present(svc.published_shifts(emp)) if s['id']==pk),None)
    if not item: raise Http404
    coworkers=[]
    if svc.workspace().show_coworkers:
        coworkers=present([s for s in svc.published_shifts() if s['event_id']==item['event_id'] and s.get('employee')!=emp.pk])
    return render(request,'scheduling/staff_shift.html',{'shift':item,'coworkers':coworkers})

@login_required
def team_schedule(request):
    emp=staff_profile(request)
    if not svc.workspace().show_coworkers: raise PermissionDenied
    locations=set(emp.locations.values_list('pk',flat=True))
    items=present([s for s in svc.published_shifts(start=timezone.now()-timedelta(days=1),end=timezone.now()+timedelta(days=30)) if s['location_id'] in locations])
    return render(request,'scheduling/team_schedule.html',{'items':items})

@login_required
@require_http_methods(['GET','POST'])
def time_off(request):
    emp=staff_profile(request);form=LeaveForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            svc.guard();q=form.save(commit=False);q.employee=emp;q.save();svc.audit(request.user,'Requested time off',q.pk)
        messages.success(request,'Request sent. Your manager will review it.');return redirect('time_off')
    return render(request,'scheduling/time_off.html',{'form':form,'requests':TimeOff.objects.filter(employee=emp).order_by('-created_at')[:30]})

@login_required
@require_http_methods(['GET','POST'])
def availability(request):
    emp=staff_profile(request);form=AvailabilityForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data
        with transaction.atomic():
            svc.guard();Availability.objects.create(employee=emp,weekday=d['weekday'] if d['kind']=='weekly' else None,date=d['date'] if d['kind']=='date' else None,starts=d['starts'],ends=d['ends']);svc.audit(request.user,'Updated availability',emp.pk)
        messages.success(request,'Unavailable time saved. Your manager can review any existing shift conflicts.');return redirect('availability')
    return render(request,'scheduling/availability.html',{'form':form,'rules':Availability.objects.filter(employee=emp)})

@login_required
@require_POST
def availability_remove(request,pk):
    emp=staff_profile(request)
    with transaction.atomic(): svc.guard();get_object_or_404(Availability,pk=pk,employee=emp).delete();svc.audit(request.user,'Removed availability block',emp.pk)
    messages.success(request,'Unavailable time removed.');return redirect('availability')

@login_required
@require_http_methods(['GET','POST'])
def my_account(request):
    emp=getattr(request.user,'employee',None)
    form=ProfileForm(request.POST or None,initial={'name':emp.name if emp else request.user.first_name or 'Administrator','email':emp.pending_email or request.user.email if emp else request.user.email,'phone':emp.phone if emp else ''})
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data;email=d['email'].lower()
        if User.objects.filter(username__iexact=email).exclude(pk=request.user.pk).exists(): form.add_error('email','That address is already in use.')
        elif email!=request.user.email and not request.user.check_password(d['current_password']):
            form.add_error('current_password','Enter your current password to change your sign-in email.')
        else:
            with transaction.atomic():
                svc.guard()
                if emp: emp.name=d['name'];emp.phone=d['phone'];emp.pending_email=email if email!=request.user.email else '';emp.save()
                else: request.user.first_name=d['name'];request.user.save(update_fields=['first_name'])
                if email!=request.user.email:
                    AccessToken.objects.filter(user=request.user,purpose='email',revoked_at__isnull=True).update(revoked_at=timezone.now())
                    token=svc.create_token(request.user,'email',days=1,payload=email)
                    # The verified account email stays unchanged until the new
                    # address receives and confirms this link.
                    svc.queue(request.user,'email:'+hashlib.sha256(token.encode()).hexdigest(),'Verify your email address',settings.APP_BASE_URL+'/verify-email/'+token+'/',recipient=email)
                    svc.audit(request.user,'Requested email verification',request.user.pk)
            messages.success(request,'Contact information saved.'+(' The new email must be verified before it is used to sign in.' if email!=request.user.email else ''));return redirect('my_account')
    return render(request,'scheduling/account.html',{'form':form,'employee':emp})

@login_required
def open_shifts(request):
    emp=staff_profile(request);slots=[]
    pub={s['id']:s for s in svc.published_shifts(start=timezone.now()) if not s.get('employee')}
    for s in Shift.objects.filter(pk__in=pub.keys(),employee__isnull=True,event__canceled=False).select_related('event__location','skill','department'):
        if not svc.eligibility(emp,s):
            item=present([pub[s.pk]])[0];item['requested']=ShiftRequest.objects.filter(employee=emp,shift=s,status='pending').exists();slots.append(item)
    return render(request,'scheduling/open_shifts.html',{'items':slots})

@login_required
@require_POST
def claim_shift(request,pk):
    emp=staff_profile(request)
    with transaction.atomic():
        svc.guard();s=get_object_or_404(Shift.objects.select_related('event__location','skill','department'),pk=pk,employee__isnull=True,event__canceled=False)
        pub=next((x for x in svc.published_shifts(start=timezone.now()) if x['id']==pk and not x.get('employee')),None)
        if not pub: raise Http404
        reasons=svc.eligibility(emp,s)
        if reasons: messages.error(request,'This shift no longer fits your availability.');return redirect('open_shifts')
        ShiftRequest.objects.get_or_create(employee=emp,shift=s,status='pending');svc.audit(request.user,'Requested open shift',pk)
    messages.success(request,'Shift requested. It will be added to your schedule after approval and publication.');return redirect('open_shifts')

@login_required
@require_http_methods(['GET','POST'])
def calendars(request):
    emp=staff_profile(request);url=None
    if request.method=='POST':
        with transaction.atomic():
            svc.guard();AccessToken.objects.filter(user=request.user,purpose='calendar',revoked_at__isnull=True).update(revoked_at=timezone.now())
            if request.POST.get('action')!='revoke':
                raw=svc.create_token(request.user,'calendar',days=365);url=settings.APP_BASE_URL+'/calendar/'+raw+'.ics'
            svc.audit(request.user,'Rotated calendar subscription' if url else 'Revoked calendar subscription',emp.pk)
        messages.success(request,'Private calendar link created. Keep it private.' if url else 'Calendar link revoked.')
    active=AccessToken.objects.filter(user=request.user,purpose='calendar',revoked_at__isnull=True,expires_at__gt=timezone.now()).exists()
    return render(request,'scheduling/calendars.html',{'calendar_url':url,'active_subscription':active})

def health(request):
    try: Workspace.objects.exists()
    except Exception: return JsonResponse({'status':'unavailable'},status=503)
    return JsonResponse({'status':'ok','service':'crewline','version':'1.0.0'})

def csrf_failure(request,reason=''):
    return render(request,'registration/csrf_failure.html',status=403)
