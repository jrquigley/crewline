from django.urls import path
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from scheduling import views as v
from scheduling.calendar import calendar_feed

urlpatterns=[
    path('',v.home,name='home'),path('healthz/',v.health,name='health'),
    path('login/',v.sign_in,name='login'),path('logout/',v.sign_out,name='logout'),
    path('password/reset/',v.reset_request,name='reset_request'),path('access/<str:token>/',v.access_link,name='access_link'),
    path('verify-email/<str:token>/',v.confirm_email,name='confirm_email'),
    path('password/change/',PasswordChangeView.as_view(template_name='registration/password_change.html',success_url='/password/changed/'),name='password_change'),
    path('password/changed/',PasswordChangeDoneView.as_view(template_name='registration/password_changed.html'),name='password_change_done'),
    path('manage/',v.dashboard,name='dashboard'),path('manage/events/new/',v.event_create,name='event_create'),
    path('manage/events/<int:pk>/',v.event_detail,name='event_detail'),path('manage/events/<int:pk>/edit/',v.event_edit,name='event_edit'),
    path('manage/events/<int:pk>/coverage/',v.add_coverage,name='add_coverage'),path('manage/events/<int:pk>/publish/',v.event_publish,name='event_publish'),
    path('manage/events/<int:pk>/cancel/',v.event_cancel,name='event_cancel'),path('manage/shifts/<int:pk>/',v.shift_edit,name='shift_edit'),
    path('manage/shifts/<int:pk>/split/',v.shift_split,name='shift_split'),
    path('manage/staff/',v.directory,name='directory'),path('manage/staff/new/',v.employee_edit,name='employee_create'),
    path('manage/staff/<int:pk>/',v.employee_detail,name='employee_detail'),path('manage/staff/<int:pk>/edit/',v.employee_edit,name='employee_edit'),
    path('manage/staff/<int:pk>/invite/',v.employee_invite,name='employee_invite'),path('manage/staff/<int:pk>/end/',v.employee_terminate,name='employee_terminate'),
    path('manage/requests/',v.requests_page,name='requests'),path('manage/requests/<str:kind>/<int:pk>/',v.request_decision,name='request_decision'),
    path('manage/settings/',v.settings_page,name='settings'),path('manage/catalog/<str:kind>/',v.catalog_add,name='catalog_add'),
    path('manage/hours/',v.hours_page,name='hours'),path('manage/history/',v.audit_page,name='audit'),
    path('manage/history/email/<int:pk>/retry/',v.retry_email,name='retry_email'),
    path('my/',v.staff_home,name='staff_home'),path('my/schedule/',v.staff_schedule,name='staff_schedule'),
    path('my/shifts/<int:pk>/',v.staff_shift,name='staff_shift'),path('my/team/',v.team_schedule,name='team_schedule'),
    path('my/time-off/',v.time_off,name='time_off'),path('my/availability/',v.availability,name='availability'),
    path('my/availability/<int:pk>/remove/',v.availability_remove,name='availability_remove'),path('my/account/',v.my_account,name='my_account'),
    path('my/open-shifts/',v.open_shifts,name='open_shifts'),path('my/open-shifts/<int:pk>/',v.claim_shift,name='claim_shift'),
    path('my/calendar/',v.calendars,name='calendars'),path('calendar/<str:token>.ics',calendar_feed,name='calendar_feed'),
]
