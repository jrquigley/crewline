import os
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from scheduling.models import Workspace, Department, Location, Skill, Employee, Event, Shift, Audit, CoverageRequirement
from scheduling import services as svc

class Command(BaseCommand):
    help='Create the first administrator and optional five fictional employees, once.'
    @transaction.atomic
    def handle(self,*args,**options):
        w=svc.workspace();svc.guard()
        if not User.objects.filter(is_superuser=True,is_active=True).exists():
            email=os.environ.get('ADMIN_EMAIL','').strip().lower();password=os.environ.get('ADMIN_PASSWORD','')
            if not email or '@' not in email or not password:
                raise CommandError('First start requires ADMIN_EMAIL and a unique ADMIN_PASSWORD of at least 15 characters. No default login is created.')
            if any(x in password.lower() for x in ('replace-me','change-me','set-a-unique','your-password')):
                raise CommandError('Replace the example ADMIN_PASSWORD before starting.')
            user=User(username=email,email=email,is_staff=True,is_superuser=True)
            try: validate_password(password,user)
            except ValidationError as error: raise CommandError('; '.join(error.messages))
            user.set_password(password);user.save();svc.audit(user,'Created initial administrator',user.pk)
            self.stdout.write('Initial administrator created. Password was not printed.')
        owner=User.objects.filter(is_superuser=True,is_active=True).first()
        if os.environ.get('SEED_SAMPLE_DATA','true').lower()!='true' or Employee.objects.exists():
            self.stdout.write('Existing records retained; no sample records added.');return
        guest=Department.objects.get_or_create(name='Guest services')[0];production=Department.objects.get_or_create(name='Production')[0]
        hall=Location.objects.get_or_create(name='Main Hall',defaults={'timezone':w.timezone})[0]
        garden=Location.objects.get_or_create(name='Garden Pavilion',defaults={'timezone':w.timezone})[0]
        welcome=Skill.objects.get_or_create(name='Guest welcome')[0];lead=Skill.objects.get_or_create(name='Event lead')[0]
        av=Skill.objects.get_or_create(name='Audio / visual')[0];firstaid=Skill.objects.get_or_create(name='First aid')[0]
        data=[('Avery Lane',[guest],[welcome,lead]),('Bennett Reed',[guest],[welcome,firstaid]),
              ('Cameron Brooks',[production],[av]),('Dana Ellis',[guest],[welcome]),('Ellis Morgan',[production,guest],[av,welcome])]
        people=[]
        for name,depts,skills in data:
            email=name.lower().replace(' ','.')+'@crewline.example'
            user=User.objects.create_user(username=email,email=email);user.set_unusable_password();user.save()
            employee=Employee.objects.create(user=user,name=name,weekly_limit=32,fictional=True)
            employee.departments.set(depts);employee.locations.set([hall,garden]);employee.skills.set(skills);people.append(employee)
        zone=ZoneInfo(w.timezone);today=timezone.now().astimezone(zone).date()
        events=[('Evening performance',today+timedelta(days=1),18,21,hall,guest,welcome,[people[1],people[0],people[3]]),
                ('Community reception',today+timedelta(days=2),12,16,garden,guest,welcome,[people[3],people[1],None]),
                ('Showcase rehearsal',today+timedelta(days=3),15,18,hall,production,av,[people[2],people[4],people[2]])]
        for name,date,start,end,location,department,skill,assignments in events:
            e=Event.objects.create(name=name,starts=datetime.combine(date,time(start),zone),ends=datetime.combine(date,time(end),zone),location=location,created_by=owner)
            for phase,employee in zip(['pre','during','post'],assignments):
                a,b=svc.bounds(e,phase);Shift.objects.create(event=e,phase=phase,department=department,skill=skill,starts=a,ends=b,employee=employee)
                CoverageRequirement.objects.create(event=e,phase=phase,department=department,skill=skill,minimum=1)
            svc.record_publication(e,owner,svc.snapshot(e))
        past=Event.objects.create(name='Previous community event',starts=datetime.combine(today-timedelta(days=7),time(13),zone),ends=datetime.combine(today-timedelta(days=7),time(16),zone),location=hall,created_by=owner)
        a,b=svc.bounds(past,'during');Shift.objects.create(event=past,phase='during',department=guest,skill=welcome,starts=a,ends=b,employee=people[0]);svc.record_publication(past,owner,svc.snapshot(past))
        Audit.objects.create(actor=owner,action='Created five fictional employee records',target='sample-data-v1',details={'fictional':True,'passwords':'unusable until privately invited'})
        self.stdout.write('Five fictional employees and sample events created. No shared employee passwords were created.')
