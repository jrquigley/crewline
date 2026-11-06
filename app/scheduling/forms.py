from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Employee, Location, Department, Skill, Workspace, TimeOff, Availability
from .services import local_datetime, eligibility, scoped_employees

class PlainLabels:
    def __init__(self,*args,**kwargs):
        kwargs.setdefault('label_suffix','')
        super().__init__(*args,**kwargs)

class SignInForm(PlainLabels,AuthenticationForm):
    username = forms.CharField(label='Email address', max_length=254, widget=forms.EmailInput(attrs={'autocomplete':'username','autofocus':True}))
    password = forms.CharField(label='Password', strip=False, max_length=256, widget=forms.PasswordInput(attrs={'autocomplete':'current-password'}))
    def clean_username(self): return self.cleaned_data['username'].strip().lower()

class ResetRequestForm(PlainLabels,forms.Form):
    email = forms.EmailField(label='Email address')

class TimeFields(PlainLabels,forms.Form):
    starts = forms.CharField(label='Start',widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    ends = forms.CharField(label='Finish',widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    def __init__(self,*args,zone='America/Los_Angeles',**kwargs): self.zone=zone;super().__init__(*args,**kwargs)
    def clean(self):
        data=super().clean();zone=data.get('location').timezone if data.get('location') else self.zone
        for field in ('starts','ends'):
            if data.get(field):
                try: data[field]=local_datetime(data[field],zone)
                except (ValidationError, ValueError) as error: self.add_error(field,str(error.messages[0]) if hasattr(error,'messages') else 'Choose a valid date and time.')
        if self.errors: return data
        if not 2000<=data['starts'].year<=2100 or not 2000<=data['ends'].year<=2100:
            self.add_error('starts','Choose a date between 2000 and 2100.');return data
        if data['ends']<=data['starts']: self.add_error('ends','Finish must be after the start. Overnight events can finish on the next date.')
        elif (data['ends']-data['starts']).total_seconds()>48*3600: self.add_error('ends','Keep each event within 48 hours.')
        return data

class EventForm(TimeFields):
    name = forms.CharField(label='Event name',max_length=120)
    location = forms.ModelChoiceField(Location.objects.all(),empty_label=None)
    department = forms.ModelChoiceField(Department.objects.all(),empty_label=None,label='Department')
    skill = forms.ModelChoiceField(Skill.objects.all(),empty_label=None,label='Skill needed')
    notes = forms.CharField(required=False,max_length=1000,label='Manager notes',widget=forms.Textarea(attrs={'rows':3}))
    external_context = forms.CharField(required=False,max_length=500,label='Nearby events or coverage context',widget=forms.Textarea(attrs={'rows':2}))
    version = forms.IntegerField(widget=forms.HiddenInput,required=False)
    field_order = ['name','location','starts','ends','department','skill','notes','external_context','version']
    def __init__(self,*args,user=None,editing=False,**kwargs):
        super().__init__(*args,**kwargs)
        if user and not user.is_superuser:
            self.fields['location'].queryset=user.employee.locations.all()
            self.fields['department'].queryset=user.employee.departments.all()
        if editing:
            self.fields.pop('department');self.fields.pop('skill')

class CoverageForm(forms.Form):
    phase = forms.ChoiceField(choices=[('pre','Before the event'),('during','During the event'),('post','After the event')])
    department = forms.ModelChoiceField(Department.objects.all(),empty_label=None)
    skill = forms.ModelChoiceField(Skill.objects.all(),empty_label=None,label='Skill needed')
    count = forms.IntegerField(min_value=1,max_value=20,initial=1,label='People needed')
    version = forms.IntegerField(widget=forms.HiddenInput)
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user and not user.is_superuser: self.fields['department'].queryset=user.employee.departments.all()

class CandidateChoice(forms.ModelChoiceField):
    def label_from_instance(self,obj):
        reasons=eligibility(obj,self.shift)
        return obj.name+' — '+(', '.join(reasons) if reasons else 'Available')

class ShiftForm(TimeFields):
    employee = CandidateChoice(Employee.objects.none(),required=False,label='Person for this shift',empty_label='Leave this shift open')
    version = forms.IntegerField(widget=forms.HiddenInput)
    field_order=['employee','starts','ends','version']
    def __init__(self,*args,user,shift,**kwargs):
        super().__init__(*args,zone=shift.event.location.timezone,**kwargs)
        self.fields['employee'].queryset=scoped_employees(user).filter(user__is_active=True,ended_at__isnull=True).order_by('name')
        self.fields['employee'].shift=shift

class EmployeeForm(PlainLabels,forms.ModelForm):
    email = forms.EmailField(label='Email address')
    manage_schedules = forms.BooleanField(required=False,label='Can manage schedules')
    class Meta:
        model=Employee
        fields=['name','email','phone','departments','locations','skills','weekly_limit','manage_schedules']
        labels={'weekly_limit':'Weekly hours limit'}
        widgets={k:forms.CheckboxSelectMultiple for k in ('departments','locations','skills')}
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs);self.actor=user
        if user and not user.is_superuser:
            self.fields.pop('manage_schedules')
            self.fields['departments'].queryset=user.employee.departments.all()
            self.fields['locations'].queryset=user.employee.locations.all()
        if self.instance.pk:
            self.fields['email'].initial=self.instance.user.email
            if 'manage_schedules' in self.fields: self.fields['manage_schedules'].initial=self.instance.user.is_staff
    def clean_email(self):
        from django.contrib.auth.models import User
        email=self.cleaned_data['email'].lower()
        qs=User.objects.filter(username__iexact=email)
        if self.instance.pk: qs=qs.exclude(pk=self.instance.user_id)
        if qs.exists(): raise forms.ValidationError('This email address already has an account.')
        return email

class ProfileForm(PlainLabels,forms.Form):
    name=forms.CharField(max_length=100,label='Full name')
    email=forms.EmailField(label='Email address')
    phone=forms.CharField(max_length=40,required=False,label='Phone number')
    current_password=forms.CharField(required=False,strip=False,label='Current password (to change email)',widget=forms.PasswordInput(attrs={'autocomplete':'current-password'}))

class LeaveForm(PlainLabels,forms.ModelForm):
    class Meta:
        model=TimeOff;fields=['first_day','last_day','note']
        widgets={'first_day':forms.DateInput(attrs={'type':'date'}),'last_day':forms.DateInput(attrs={'type':'date'}),'note':forms.Textarea(attrs={'rows':3})}
        labels={'first_day':'First day','last_day':'Last day','note':'Note for your manager (optional)'}
    def clean(self):
        d=super().clean()
        if d.get('first_day') and d.get('last_day'):
            if d['last_day']<d['first_day']: self.add_error('last_day','Choose a date on or after the first day.')
            if (d['last_day']-d['first_day']).days>366: self.add_error('last_day','Request no more than one year at a time.')
            if d['first_day']<timezone.localdate(): self.add_error('first_day','Choose today or a future date.')
        return d

class AvailabilityForm(PlainLabels,forms.Form):
    kind=forms.ChoiceField(choices=[('weekly','Every week'),('date','One date only')],label='How often?')
    weekday=forms.TypedChoiceField(choices=list(enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])),coerce=int,required=False,label='Day of the week')
    date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}),label='Date')
    starts=forms.TimeField(widget=forms.TimeInput(attrs={'type':'time'}),label='Unavailable from')
    ends=forms.TimeField(widget=forms.TimeInput(attrs={'type':'time'}),label='Unavailable until')
    def clean(self):
        d=super().clean()
        if d.get('kind')=='date' and not d.get('date'): self.add_error('date','Choose the date.')
        if d.get('kind')=='weekly' and d.get('weekday')=='': self.add_error('weekday','Choose a weekday.')
        if d.get('starts')==d.get('ends') and d.get('starts'): self.add_error('ends','Choose a different finish time. A finish before the start means overnight.')
        return d

class WorkspaceForm(PlainLabels,forms.ModelForm):
    class Meta:
        model=Workspace
        fields=['name','timezone','pre_minutes','post_minutes','handover_minutes','travel_minutes','updates_enabled','digest_enabled','digest_day','digest_time','show_coworkers']
        labels={'name':'Organization name','timezone':'Scheduling timezone','pre_minutes':'Setup before an event (minutes)',
                'post_minutes':'Close after an event (minutes)','handover_minutes':'Handover overlap (minutes)',
                'travel_minutes':'Travel between locations (minutes)','updates_enabled':'Email staff when published shifts change',
                'digest_enabled':'Email next week’s schedule once a week','digest_day':'Weekly email day','digest_time':'Weekly email time',
                'show_coworkers':'Let staff see coworkers’ published shifts'}
        widgets={'digest_time':forms.TimeInput(attrs={'type':'time'}),'digest_day':forms.Select(choices=list(enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])))}
    def clean_timezone(self):
        v=self.cleaned_data['timezone']
        try: ZoneInfo(v)
        except ZoneInfoNotFoundError: raise forms.ValidationError('Use an IANA timezone such as America/Los_Angeles.')
        return v
    def clean(self):
        d=super().clean()
        if d.get('post_minutes',0)<d.get('handover_minutes',0): self.add_error('post_minutes','Closing coverage must be at least as long as the handover.')
        return d
