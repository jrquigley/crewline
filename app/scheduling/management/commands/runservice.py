import logging
import threading
import time
from django.core.management.base import BaseCommand
from django.core.wsgi import get_wsgi_application
from waitress import serve
from scheduling.delivery import tick

class Command(BaseCommand):
    help='Run the production WSGI application and bounded schedule email worker.'
    def add_arguments(self,parser):
        parser.add_argument('--port',type=int,default=3000)
        parser.add_argument('--host',default='0.0.0.0')
        parser.add_argument('--no-worker',action='store_true')
    def handle(self,*args,**options):
        def worker():
            while True:
                try: tick()
                except Exception: logging.getLogger('crewline').error('Schedule worker tick failed; it will retry.')
                time.sleep(30)
        if not options['no_worker']: threading.Thread(target=worker,daemon=True,name='schedule-worker').start()
        serve(get_wsgi_application(),host=options['host'],port=options['port'],threads=4,max_request_body_size=65536,
              ident='Crewline',clear_untrusted_proxy_headers=False)
