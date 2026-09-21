import os
import sys
import time
import django
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from globalhost import GlobalHostApp

if not settings.configured:
    settings.configure(
        ROOT_URLCONF=__name__,
        SECRET_KEY='super-secret-key-for-named-tunnel',
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
    )
    django.setup()

def api_root(request):
    return JsonResponse({
        "status": "success",
        "message": "Django is live on a permanent Named Tunnel!"
    })

urlpatterns = [
    path('', api_root),
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    else:
        host = GlobalHostApp()

        # PRO TIP: You can paste the ENTIRE manual command from Cloudflare here!
        # Example: "cloudflared tunnel run --token eyJhIjoi..."
        # The code will automatically extract just the token for you.
        token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "cloudflared tunnel run --token YOUR_TOKEN_HERE")

        if host.bg_launch("django", __file__, port=8002, token=token):
            print(f"\nDjango is live on your custom domain!")
            print(f"URL: {host.get_url()}")
            print("Press Ctrl+C to shut down.\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                host.stop()
