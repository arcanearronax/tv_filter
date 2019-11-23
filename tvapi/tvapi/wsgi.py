"""
WSGI config for tvapi project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvapi.settings')

os.environ['SKEY'] = '%p7*o#s$zks3015(s&txjz-mw8%#z!+na4!b9(qfj^6=891y@@'
os.environ['AHOST'] = 'tvapi.arcanedomain.duckdns.org'
os.environ['BHOST'] = '10.0.0.4'
os.environ['userName'] = 'webmaster'
os.environ['userPass'] = 'Dexter313!'


application = get_wsgi_application()

