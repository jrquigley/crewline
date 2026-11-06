from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

class Workspace(models.Model):
    name = models.CharField(max_length=100, default='Crewline')
    timezone = models.CharField(max_length=64, default='America/Los_Angeles')
    pre_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1),MaxValueValidator(480)])
    post_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1),MaxValueValidator(480)])
    handover_minutes = models.PositiveIntegerField(default=15, validators=[MaxValueValidator(120)])
    travel_minutes = models.PositiveIntegerField(default=30, validators=[MaxValueValidator(240)])
    digest_day = models.PositiveSmallIntegerField(default=6, validators=[MaxValueValidator(6)])
    digest_time = models.TimeField(default='17:00')
    digest_enabled = models.BooleanField(default=True)
    updates_enabled = models.BooleanField(default=True)
    show_coworkers = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=0)

class Department(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    timezone = models.CharField(max_length=64, default='America/Los_Angeles')
    def __str__(self): return self.name

class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='employee')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=40, blank=True)
    pending_email = models.EmailField(blank=True)
    departments = models.ManyToManyField(Department)
    locations = models.ManyToManyField(Location)
    skills = models.ManyToManyField(Skill, blank=True)
    weekly_limit = models.PositiveSmallIntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(168)])
    ended_at = models.DateTimeField(null=True, blank=True)
    fictional = models.BooleanField(default=False)
    def __str__(self): return self.name
    @property
    def initials(self): return ''.join(w[0] for w in self.name.split()[:2]).upper()
    @property
    def active(self): return self.user.is_active and self.ended_at is None

class Event(models.Model):
    name = models.CharField(max_length=120)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    notes = models.CharField(max_length=1000, blank=True)
    version = models.PositiveIntegerField(default=1)
    published_version = models.PositiveIntegerField(default=0)
    published_snapshot = models.JSONField(default=dict)
    canceled = models.BooleanField(default=False)
    external_context = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    class Meta:
        ordering = ['starts', 'pk']
        constraints = [models.CheckConstraint(condition=Q(ends__gt=models.F('starts')), name='event_positive_interval')]
    @property
    def dirty(self): return self.version != self.published_version

class Shift(models.Model):
    PHASES = [('pre', 'Before the event'), ('during', 'During the event'), ('post', 'After the event')]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='shifts')
    phase = models.CharField(max_length=10, choices=PHASES)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True)
    class Meta:
        ordering = ['starts', 'pk']
        constraints = [models.CheckConstraint(condition=Q(ends__gt=models.F('starts')), name='shift_positive_interval')]
    @property
    def hours(self): return (self.ends - self.starts).total_seconds() / 3600

class CoverageRequirement(models.Model):
    event = models.ForeignKey(Event,on_delete=models.CASCADE,related_name='requirements')
    phase = models.CharField(max_length=10,choices=Shift.PHASES)
    department = models.ForeignKey(Department,on_delete=models.PROTECT)
    skill = models.ForeignKey(Skill,on_delete=models.PROTECT)
    minimum = models.PositiveSmallIntegerField(default=1,validators=[MinValueValidator(1),MaxValueValidator(200)])
    class Meta:
        constraints=[models.UniqueConstraint(fields=['event','phase','department','skill'],name='one_coverage_requirement')]

class Publication(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class TimeOff(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    first_day = models.DateField()
    last_day = models.DateField()
    note = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=12, default='pending', choices=[('pending','Pending'),('approved','Approved'),('declined','Declined'),('closed','Closed')])
    created_at = models.DateTimeField(auto_now_add=True)

class Availability(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    starts = models.TimeField()
    ends = models.TimeField()

class ShiftRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['employee','shift'], condition=Q(status='pending'), name='one_pending_claim')]

class AccessToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=20)
    payload = models.CharField(max_length=254, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

class Audit(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at', '-pk']

class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

class Outbox(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    key = models.CharField(max_length=160, unique=True)
    subject = models.CharField(max_length=160)
    recipient = models.EmailField(blank=True)
    body = models.TextField()
    status = models.CharField(max_length=12, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    claimed_at = models.DateTimeField(null=True)
    error = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(null=True)
