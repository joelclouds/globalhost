import os
import sys
import time
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from globalhost import GlobalHostApp

if not settings.configured:
    settings.configure(
        ROOT_URLCONF=__name__,
        SECRET_KEY='super-secret-key-for-example-only',
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
    )
    django.setup()

def webpage_root(request):
    html = """
    <html>
        <head><title>GlobalHost Django</title></head>
        <body><h1>Hello from Django!</h1><p>Served via Cloudflare Tunnel.</p></body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    path('', webpage_root),
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    else:
        host = GlobalHostApp()
        if host.bg_launch("django", __file__, port=8003):
            print(f"\nDjango Webpage is live!")
            print(f"Public URL: {host.get_url()}")
            print("Press Ctrl+C to shut down.\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                host.stop()
