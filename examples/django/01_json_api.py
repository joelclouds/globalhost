import os
import sys
import time
import django
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from globalhost import GlobalHostApp

# 1. Guard the configuration so it only runs once
if not settings.configured:
    settings.configure(
        ROOT_URLCONF=__name__,
        SECRET_KEY='super-secret-key-for-example-only',
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
    )
    django.setup()

def api_root(request):
    return JsonResponse({"status": "success", "message": "Django JSON endpoint is live!"})

urlpatterns = [
    path('', api_root),
]

if __name__ == "__main__":
    # 2. If GlobalHost calls this script with 'runserver', act as manage.py
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    else:
        # 3. Otherwise, we are the entry point. Launch the tunnel.
        host = GlobalHostApp()
        if host.bg_launch("django", __file__, port=8002):
            print(f"\nDjango is live in the background!")
            print(f"Public URL: {host.get_url()}")
            print("Press Ctrl+C to shut down.\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                host.stop()
