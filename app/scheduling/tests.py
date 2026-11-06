import hashlib
import io
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, time, timezone as utc
from unittest.mock import patch
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db import connections
from django.test import TestCase, Client, override_settings, SimpleTestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from .models import *
from . import services as svc
from .delivery import create_digests, deliver_one

PASSWORD='Testing-only-copper-garden-71!'

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.w=Workspace.objects.create(pk=1)
        cls.admin=User.objects.create_superuser(username='owner@example.test',email='owner@example.test',password=PASSWORD)
        cls.dep=Department.objects.create(name='Guest services');cls.other_dep=Department.objects.create(name='Production')
        cls.loc=Location.objects.create(name='Main Hall');cls.other_loc=Location.objects.create(name='Other location')
        cls.skill=Skill.objects.create(name='Guest welcome');cls.other_skill=Skill.objects.create(name='Audio / visual')
        cls.people=[]
        for name in ['Avery Lane','Bennett Reed','Dana Ellis']:
            user=User.objects.create_user(username=name.lower().replace(' ','.')+'@example.test',email=name.lower().replace(' ','.')+'@example.test',password=PASSWORD)
            e=Employee.objects.create(user=user,name=name,weekly_limit=40)
            e.departments.add(cls.dep);e.locations.add(cls.loc);e.skills.add(cls.skill);cls.people.append(e)
        now=timezone.now()+timedelta(days=2);cls.start=now.replace(hour=18,minute=0,second=0,microsecond=0)
        cls.event=Event.objects.create(name='Evening performance',location=cls.loc,starts=cls.start,ends=cls.start+timedelta(hours=3),created_by=cls.admin)
        for phase,employee in zip(['pre','during','post'],cls.people):
            a,b=svc.bounds(cls.event,phase);Shift.objects.create(event=cls.event,phase=phase,department=cls.dep,skill=cls.skill,starts=a,ends=b,employee=employee)
    def login_admin(self): self.client.force_login(self.admin)
    def login_staff(self): self.client.force_login(self.people[0].user)
    def publish(self): return svc.publish(self.event.pk,self.admin,Event.objects.get(pk=self.event.pk).version)

    def test_anonymous_is_redirected(self):
        for url in ['/manage/','/manage/staff/','/manage/hours/','/my/','/my/account/','/my/calendar/']:
            self.assertEqual(self.client.get(url).status_code,302,url)
    def test_no_public_signup(self): self.assertEqual(self.client.get('/signup/').status_code,404)
    def test_login_generic_error_and_valid_login(self):
        r=self.client.post('/login/',{'username':'missing@example.test','password':'wrong'});self.assertEqual(r.status_code,200)
        r=self.client.post('/login/',{'username':self.admin.username,'password':PASSWORD});self.assertRedirects(r,'/',fetch_redirect_response=False)
    def test_external_next_redirect_rejected(self):
        r=self.client.post('/login/?next=https://attacker.example/',{'username':self.admin.username,'password':PASSWORD});self.assertEqual(r['Location'],'/')
    def test_login_rate_limited(self):
        for _ in range(5): self.client.post('/login/',{'username':self.admin.username,'password':'wrong'})
        r=self.client.post('/login/',{'username':self.admin.username,'password':PASSWORD});self.assertEqual(r.status_code,429);self.assertNotIn('_auth_user_id',self.client.session)
    def test_csrf_required_for_login_and_mutations(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/login/',{'username':self.admin.username,'password':PASSWORD}).status_code,403)
        c.force_login(self.admin);self.assertEqual(c.post(reverse('event_cancel',args=[self.event.pk]),{'version':1}).status_code,403)
    @override_settings(SESSION_COOKIE_SECURE=True,CSRF_COOKIE_SECURE=True)
    def test_valid_https_csrf_login_and_secure_session_cookie(self):
        c=Client(enforce_csrf_checks=True);c.get('/login/',secure=True)
        r=c.post('/login/',{'username':self.admin.username,'password':PASSWORD,'csrfmiddlewaretoken':c.cookies['csrftoken'].value},secure=True,HTTP_ORIGIN='https://testserver')
        self.assertEqual(r.status_code,302);self.assertTrue(r.cookies['sessionid']['secure']);self.assertTrue(r.cookies['sessionid']['httponly']);self.assertEqual(r.cookies['sessionid']['samesite'],'Lax')
    def test_logout_is_post_only(self):
        self.login_admin();self.assertEqual(self.client.get('/logout/').status_code,405)
        self.assertEqual(self.client.post('/logout/').status_code,302);self.assertNotIn('_auth_user_id',self.client.session)
    def test_staff_cannot_manage(self):
        self.login_staff()
        for url in ['/manage/','/manage/staff/','/manage/settings/','/manage/history/','/manage/hours/']:
            self.assertEqual(self.client.get(url).status_code,403,url)
        self.assertEqual(self.client.post(reverse('event_publish',args=[self.event.pk]),{'version':1}).status_code,403)
    def test_scoped_manager_cannot_access_other_location(self):
        manager=self.people[0];manager.user.is_staff=True;manager.user.save()
        other=Event.objects.create(name='Private outside event',location=self.other_loc,starts=self.start,ends=self.start+timedelta(hours=2),created_by=self.admin)
        Shift.objects.create(event=other,phase='during',department=self.dep,skill=self.skill,starts=other.starts,ends=other.ends)
        self.client.force_login(manager.user);self.assertEqual(self.client.get(reverse('event_detail',args=[other.pk])).status_code,404)
        self.assertFalse(svc.can_manage(manager.user,other))
    def test_manager_cannot_publish_mixed_scope_event(self):
        manager=self.people[0];manager.user.is_staff=True;manager.user.save()
        Shift.objects.create(event=self.event,phase='during',department=self.other_dep,skill=self.other_skill,starts=self.start,ends=self.event.ends)
        self.assertFalse(svc.can_manage(manager.user,self.event))
    def test_manager_cannot_remove_out_of_scope_employee_memberships(self):
        manager=self.people[0];manager.user.is_staff=True;manager.user.save()
        shared=self.people[1];shared.departments.add(self.other_dep);shared.locations.add(self.other_loc)
        self.client.force_login(manager.user)
        self.assertEqual(self.client.get(reverse('employee_edit',args=[shared.pk])).status_code,403)
        self.assertEqual(self.client.post(reverse('employee_edit',args=[shared.pk]),{'name':'Changed'}).status_code,403)
        self.assertEqual(shared.departments.count(),2);self.assertEqual(shared.locations.count(),2)
        self.assertTrue(svc.can_edit_employee(self.admin,shared))
    def test_private_bearer_urls_redacted_in_application_logs(self):
        import logging
        from .safe_logging import PrivateURLFilter
        record=logging.LogRecord('django.request',logging.ERROR,'',0,'Unavailable: %s',('/calendar/private-test-secret.ics',),None)
        PrivateURLFilter().filter(record)
        self.assertNotIn('private-test-secret',record.getMessage());self.assertIn('[redacted]',record.getMessage())
    def test_manager_pages_render(self):
        self.login_admin()
        for url in ['/manage/','/manage/events/new/','/manage/staff/','/manage/staff/new/','/manage/requests/','/manage/settings/','/manage/hours/','/manage/history/',reverse('event_detail',args=[self.event.pk]),reverse('event_edit',args=[self.event.pk]),reverse('event_publish',args=[self.event.pk]),reverse('employee_detail',args=[self.people[0].pk]),reverse('employee_edit',args=[self.people[0].pk]),reverse('shift_edit',args=[self.event.shifts.first().pk])]:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_staff_pages_render(self):
        self.publish();self.login_staff()
        for url in ['/my/','/my/schedule/','/my/team/','/my/time-off/','/my/availability/','/my/account/','/my/open-shifts/','/my/calendar/',reverse('staff_shift',args=[self.event.shifts.first().pk])]:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_private_responses_and_security_headers(self):
        self.login_admin();r=self.client.get('/manage/');self.assertIn('no-store',r['Cache-Control']);self.assertIn("script-src 'self'",r['Content-Security-Policy']);self.assertEqual(r['X-Frame-Options'],'DENY')
    def test_drafts_hidden_and_publish_updates(self):
        self.assertEqual(svc.published_shifts(self.people[0]),[]);self.publish();self.assertEqual(len(svc.published_shifts(self.people[0])),1)
        s=self.event.shifts.get(phase='pre');old=s.ends
        svc.assign(s.pk,self.admin,1,self.people[0],s.starts,s.ends+timedelta(minutes=15))
        self.assertEqual(svc.published_shifts(self.people[0])[0]['ends'],old)
        self.publish();self.assertEqual(svc.published_shifts(self.people[0])[0]['ends'],old+timedelta(minutes=15))
    def test_stale_edits_rejected(self):
        s=self.event.shifts.first();svc.assign(s.pk,self.admin,1,None,s.starts,s.ends)
        with self.assertRaises(ValidationError): svc.assign(s.pk,self.admin,1,self.people[0],s.starts,s.ends)
        with self.assertRaises(ValidationError): svc.publish(self.event.pk,self.admin,1)
    def test_leave_updates_snapshot_without_marking_unrelated_draft_published(self):
        self.publish();self.event.refresh_from_db();self.event.name='Private draft title';self.event.version+=1;self.event.save()
        day=self.event.starts.astimezone(ZoneInfo(self.w.timezone)).date()
        leave=TimeOff.objects.create(employee=self.people[0],first_day=day,last_day=day)
        svc.decide_leave(leave.pk,self.admin,True);self.event.refresh_from_db()
        self.assertTrue(self.event.dirty);self.assertEqual(self.event.published_snapshot['name'],'Evening performance')
        job=Outbox.objects.filter(user=self.people[0].user,key__startswith='event:').last()
        body=svc.cipher().decrypt(job.body.encode()).decode()
        self.assertNotIn('Private draft title',body);self.assertIn('Previously:',body)
        self.publish();self.event.refresh_from_db();self.assertFalse(self.event.dirty)
        self.assertEqual(self.event.published_snapshot['name'],'Private draft title')
    def test_termination_preserves_unrelated_draft_publication_work(self):
        self.publish();self.event.refresh_from_db();self.event.name='Private draft title';self.event.version+=1;self.event.save()
        svc.terminate(self.people[0].pk,self.admin);self.event.refresh_from_db()
        self.assertTrue(self.event.dirty);self.assertEqual(self.event.published_snapshot['name'],'Evening performance')
        self.assertIsNone(self.event.published_snapshot['shifts'][0]['employee'])
        self.publish();self.event.refresh_from_db();self.assertEqual(self.event.published_snapshot['name'],'Private draft title')
    def test_skill_location_department_checks(self):
        s=self.event.shifts.first();p=self.people[0];p.skills.clear();self.assertIn('Needs Guest welcome',svc.eligibility(p,s))
        p.locations.clear();p.departments.clear();r=svc.eligibility(p,s);self.assertIn('Different location',r);self.assertIn('Different department',r)
    def test_overlap_and_travel_checks(self):
        s=self.event.shifts.get(phase='during');s.employee=self.people[0]
        self.assertIn('Overlapping shift',svc.eligibility(self.people[0],s))
        s.starts=self.event.shifts.get(phase='pre').ends+timedelta(minutes=5);s.ends=s.starts+timedelta(hours=1);s.event.location=self.other_loc;self.people[0].locations.add(self.other_loc)
        self.assertIn('Not enough travel time',svc.eligibility(self.people[0],s))
    def test_hour_limit(self):
        p=self.people[0];p.weekly_limit=1;p.save();self.assertIn('Weekly hours limit exceeded',svc.eligibility(p,self.event.shifts.first()))
    def test_approved_leave_and_recurring_availability(self):
        s=self.event.shifts.first();p=self.people[0];d=s.starts.astimezone(ZoneInfo(self.w.timezone)).date()
        TimeOff.objects.create(employee=p,first_day=d,last_day=d,status='approved');self.assertIn('Approved time off',svc.eligibility(p,s));TimeOff.objects.all().delete()
        Availability.objects.create(employee=p,weekday=d.weekday(),starts=time(0),ends=time(23,59));self.assertIn('Outside availability',svc.eligibility(p,s))
    def test_overnight_availability(self):
        p=self.people[0];zone=ZoneInfo(self.w.timezone);a=datetime.combine(timezone.localdate()+timedelta(days=4),time(1),zone);b=a+timedelta(hours=1)
        Availability.objects.create(employee=p,date=a.date()-timedelta(days=1),starts=time(22),ends=time(3))
        self.assertEqual(svc.unavailable(p,a,b),'Outside availability')
    def test_dst_nonexistent_and_ambiguous(self):
        for value in ['2027-03-14T02:30','2026-11-01T01:30']:
            with self.assertRaises(ValidationError): svc.local_datetime(value,'America/Los_Angeles')
    def test_invalid_time_and_short_coverage_block_publish(self):
        s=self.event.shifts.first()
        with self.assertRaises(ValidationError): svc.assign(s.pk,self.admin,1,None,s.ends,s.starts)
        s.ends-=timedelta(minutes=30);s.save()
        with self.assertRaises(ValidationError): self.publish()
    def test_database_positive_interval_constraint(self):
        with self.assertRaises(IntegrityError),transaction.atomic(): Event.objects.create(name='Bad',location=self.loc,starts=self.start,ends=self.start,created_by=self.admin)
    def test_open_shift_claim_and_competing_approval(self):
        s=self.event.shifts.get(phase='post');s.employee=None;s.save();self.publish()
        q=ShiftRequest.objects.create(employee=self.people[2],shift=s);svc.decide_claim(q.pk,self.admin,True)
        other=ShiftRequest.objects.create(employee=self.people[1],shift=s)
        with self.assertRaises(ValidationError): svc.decide_claim(other.pk,self.admin,True)
        s.refresh_from_db();self.assertEqual(s.employee,self.people[2]);self.assertIsNone(svc.published_shifts()[-1]['employee'])
    def test_staff_cannot_request_unpublished_slot(self):
        s=self.event.shifts.get(phase='pre');s.employee=None;s.save();self.login_staff()
        self.assertEqual(self.client.post(reverse('claim_shift',args=[s.pk])).status_code,404)
    def test_team_schedule_does_not_leak_contacts_or_notes(self):
        self.publish();self.login_staff();r=self.client.get('/my/team/');self.assertNotContains(r,self.people[1].user.email);self.assertNotContains(r,'phone')
        self.w.show_coworkers=False;self.w.save();self.assertEqual(self.client.get('/my/team/').status_code,403)
    def test_staff_cannot_read_others_shift(self):
        self.publish();self.login_staff();s=self.event.shifts.get(phase='during');self.assertEqual(self.client.get(reverse('staff_shift',args=[s.pk])).status_code,404)
    def test_time_off_approval_reopens_published_shift(self):
        self.publish();p=self.people[0];s=self.event.shifts.get(phase='pre');d=s.starts.astimezone(ZoneInfo(self.w.timezone)).date()
        q=TimeOff.objects.create(employee=p,first_day=d,last_day=d,note='Private reason');svc.decide_leave(q.pk,self.admin,True)
        s.refresh_from_db();self.assertIsNone(s.employee_id);self.assertEqual(svc.published_shifts(p),[]);self.assertTrue(Publication.objects.filter(snapshot__shifts__0__employee=p.pk).exists())
    def test_terminate_revokes_active_session_and_calendar_and_retains_history(self):
        self.publish();p=self.people[0];self.client.force_login(p.user);raw=svc.create_token(p.user,'calendar',365)
        self.assertEqual(self.client.get(reverse('calendar_feed',args=[raw])).status_code,200)
        svc.terminate(p.pk,self.admin)
        self.assertEqual(self.client.get('/my/').status_code,302);self.assertEqual(self.client.get(reverse('calendar_feed',args=[raw])).status_code,401)
        self.assertTrue(Employee.objects.filter(pk=p.pk).exists());self.assertTrue(Publication.objects.filter(snapshot__shifts__0__employee=p.pk).exists());self.assertIsNone(Shift.objects.get(pk=self.event.shifts.first().pk).employee_id)
        self.assertFalse(Outbox.objects.filter(user=p.user,status='pending').exists())
    def test_cannot_terminate_self_or_administrator(self):
        p=self.people[0];p.user.is_superuser=True;p.user.save()
        with self.assertRaises(ValidationError): svc.terminate(p.pk,self.admin)
    def test_invitation_is_hashed_one_use_and_can_set_password(self):
        p=self.people[0];raw=svc.create_token(p.user,'invite')
        self.assertFalse(AccessToken.objects.filter(digest=raw).exists());self.assertEqual(len(AccessToken.objects.first().digest),64)
        r=self.client.post(reverse('access_link',args=[raw]),{'new_password1':PASSWORD+'new','new_password2':PASSWORD+'new'});self.assertEqual(r.status_code,302)
        self.assertEqual(self.client.get(reverse('access_link',args=[raw])).status_code,400)
        self.assertTrue(User.objects.get(pk=p.user_id).check_password(PASSWORD+'new'))
    def test_invitation_expiration_and_termination(self):
        p=self.people[0];raw=svc.create_token(p.user,'invite',days=-1);self.assertEqual(self.client.get(reverse('access_link',args=[raw])).status_code,400)
        raw=svc.create_token(p.user,'invite');svc.terminate(p.pk,self.admin);self.assertEqual(self.client.get(reverse('access_link',args=[raw])).status_code,400)
    def test_password_policy_blocks_weak(self):
        raw=svc.create_token(self.people[0].user,'invite');r=self.client.post(reverse('access_link',args=[raw]),{'new_password1':'weak','new_password2':'weak'});self.assertEqual(r.status_code,200);self.assertContains(r,'15 characters')
    def test_email_change_pending_until_verified(self):
        self.login_staff();p=self.people[0];r=self.client.post('/my/account/',{'name':p.name,'email':'new-address@example.test','phone':'test contact','current_password':PASSWORD});self.assertEqual(r.status_code,302)
        p.user.refresh_from_db();self.assertNotEqual(p.user.email,'new-address@example.test');grant=AccessToken.objects.get(purpose='email');self.assertEqual(grant.payload,'new-address@example.test')
        job=Outbox.objects.get(subject='Verify your email address');self.assertEqual(job.recipient,'new-address@example.test');self.assertNotIn('/verify-email/',job.body)
    def test_calendar_only_own_published_and_cancellation(self):
        self.publish();p=self.people[0];raw=svc.create_token(p.user,'calendar',365);url=reverse('calendar_feed',args=[raw]);r=self.client.get(url)
        self.assertContains(r,'BEGIN:VCALENDAR');self.assertContains(r,'STATUS:CONFIRMED');self.assertNotContains(r,self.people[1].name);self.assertIn('no-store',r['Cache-Control'])
        s=self.event.shifts.get(phase='pre');svc.assign(s.pk,self.admin,1,None,s.starts,s.ends);self.publish();r=self.client.get(url);self.assertContains(r,'STATUS:CANCELLED');self.assertContains(r,'SEQUENCE:2')
    def test_calendar_token_rotation(self):
        self.login_staff();raw=svc.create_token(self.people[0].user,'calendar',365);self.client.post('/my/calendar/',{'action':'create'});self.assertEqual(self.client.get(reverse('calendar_feed',args=[raw])).status_code,401)
    def test_outbox_payload_encrypted_and_idempotent(self):
        svc.queue(self.admin,'unique','Subject','private access secret');svc.queue(self.admin,'unique','Subject','private access secret')
        self.assertEqual(Outbox.objects.filter(key='unique').count(),1);job=Outbox.objects.get(key='unique');self.assertNotIn('private access secret',job.body);self.assertEqual(svc.cipher().decrypt(job.body.encode()).decode(),'private access secret')
    @override_settings(SMTP_CONFIGURED=True,EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_delivery_and_inactive_suppression(self):
        svc.queue(self.people[0].user,'send','Test','Body');self.assertTrue(deliver_one());self.assertEqual(len(mail.outbox),1)
        p=self.people[1];svc.queue(p.user,'inactive','Test','Body');p.user.is_active=False;p.user.save();deliver_one();self.assertEqual(len(mail.outbox),1);self.assertEqual(Outbox.objects.get(key='inactive').status,'canceled')
    @override_settings(SMTP_CONFIGURED=True,EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_fictional_recipients_never_emailed(self):
        u=User.objects.create_user('fictional@crewline.example',email='fictional@crewline.example');svc.queue(u,'fictional','Test','Body');deliver_one();self.assertEqual(len(mail.outbox),0);self.assertEqual(Outbox.objects.get(key='fictional').status,'blocked')
    @override_settings(SMTP_CONFIGURED=True)
    def test_ambiguous_provider_failure_is_not_blindly_retried(self):
        svc.queue(self.admin,'failure','Test','Body')
        with patch('scheduling.delivery.send_mail',side_effect=RuntimeError('private error')): deliver_one()
        self.assertEqual(Outbox.objects.get(key='failure').status,'review');self.assertFalse(deliver_one())
    def test_weekly_digest_idempotent(self):
        zone=ZoneInfo(self.w.timezone);now=datetime(2026,11,8,18,0,tzinfo=zone)
        self.assertEqual(create_digests(now),3);self.assertEqual(create_digests(now),0)
        self.assertTrue(Outbox.objects.filter(key__contains='2026-11-09').exists())
    def test_csv_formula_escaped(self):
        p=self.people[0];p.name='=SUM(1,1)';p.save();self.login_admin();r=self.client.get('/manage/hours/?format=csv');self.assertIn("'=SUM",r.content.decode())
    def test_xss_is_escaped(self):
        self.event.name='<script>alert(1)</script>';self.event.save();self.login_admin();r=self.client.get('/manage/');self.assertContains(r,'&lt;script&gt;');self.assertNotContains(r,'<script>alert(1)</script>')
    def test_health_is_non_sensitive(self):
        r=self.client.get('/healthz/');self.assertEqual(r.status_code,200);self.assertNotIn('database',r.json());self.assertNotIn('secret',r.content.decode())
    def test_new_event_overnight(self):
        self.login_admin();day=timezone.localdate()+timedelta(days=4)
        r=self.client.post('/manage/events/new/',{'name':'Overnight build','location':self.loc.pk,'department':self.dep.pk,'skill':self.skill.pk,'starts':str(day)+'T22:00','ends':str(day+timedelta(days=1))+'T02:00'})
        self.assertEqual(r.status_code,302);e=Event.objects.get(name='Overnight build');self.assertEqual(e.shifts.count(),3);self.assertGreater(e.ends,e.starts)
    def test_email_change_requires_current_password(self):
        self.login_staff();p=self.people[0];r=self.client.post('/my/account/',{'name':p.name,'email':'different@example.test','phone':''})
        self.assertEqual(r.status_code,200);self.assertFalse(AccessToken.objects.filter(purpose='email').exists())
    def test_shift_split_preserves_headcount_and_requires_handover(self):
        s=self.event.shifts.get(phase='during');s.employee=None;s.save()
        cut=s.starts+timedelta(hours=1);second=svc.split_shift(s.pk,self.admin,1,cut)
        s.refresh_from_db();self.assertEqual(s.ends,cut+timedelta(minutes=15));self.assertEqual(second.starts,cut)
        self.assertEqual(CoverageRequirement.objects.get(event=self.event,phase='during').minimum,1)
        self.assertEqual(svc.event_issues(Event.objects.get(pk=self.event.pk)),[])
        second.starts+=timedelta(minutes=30);second.save();self.assertTrue(svc.event_issues(Event.objects.get(pk=self.event.pk)))
    def test_invalid_split_is_rejected(self):
        s=self.event.shifts.first()
        with self.assertRaises(ValidationError): svc.split_shift(s.pk,self.admin,1,s.starts-timedelta(minutes=1))

class RealPasswordHashTests(SimpleTestCase):
    def test_production_hasher_is_expensive_and_verifiable(self):
        hasher=PBKDF2PasswordHasher();self.assertGreaterEqual(hasher.iterations,1_000_000)
        encoded=hasher.encode(PASSWORD,hasher.salt());self.assertTrue(hasher.verify(PASSWORD,encoded));self.assertNotIn(PASSWORD,encoded)

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BootstrapTests(TestCase):
    def test_exactly_five_fictional_profiles_no_default_employee_passwords_and_repeat_safe(self):
        User.objects.create_superuser(username='owner@example.test',email='owner@example.test',password=PASSWORD)
        call_command('bootstrap',stdout=io.StringIO());self.assertEqual(Employee.objects.count(),5)
        self.assertTrue(all(not e.user.has_usable_password() and e.fictional for e in Employee.objects.select_related('user')))
        count=Event.objects.count();call_command('bootstrap',stdout=io.StringIO());self.assertEqual(Employee.objects.count(),5);self.assertEqual(Event.objects.count(),count)

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrentAssignmentTests(TransactionTestCase):
    def setUp(self):
        Workspace.objects.create(pk=1)
        self.admin=User.objects.create_superuser(username='owner@example.test',password=PASSWORD)
        self.dep=Department.objects.create(name='Guest services');self.loc=Location.objects.create(name='Hall');self.skill=Skill.objects.create(name='Welcome')
        user=User.objects.create_user(username='staff@example.test',password=PASSWORD)
        self.emp=Employee.objects.create(user=user,name='Concurrent employee');self.emp.departments.add(self.dep);self.emp.locations.add(self.loc);self.emp.skills.add(self.skill)
        self.slots=[]
        for title in ['First event','Second event']:
            a=timezone.now()+timedelta(days=3);b=a+timedelta(hours=2)
            event=Event.objects.create(name=title,starts=a,ends=b,location=self.loc,created_by=self.admin)
            self.slots.append(Shift.objects.create(event=event,phase='during',department=self.dep,skill=self.skill,starts=a,ends=b))
    def test_competing_overlapping_assignments_only_one_commits(self):
        barrier=threading.Barrier(2)
        def attempt(pk):
            try:
                slot=Shift.objects.get(pk=pk);actor=User.objects.get(pk=self.admin.pk);employee=Employee.objects.get(pk=self.emp.pk)
                barrier.wait(timeout=5)
                try: svc.assign(pk,actor,1,employee,slot.starts,slot.ends);return 'assigned'
                except ValidationError: return 'rejected'
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(attempt,[s.pk for s in self.slots]))
        self.assertEqual(sorted(results),['assigned','rejected']);self.assertEqual(Shift.objects.filter(employee=self.emp).count(),1)
