import os
import sys
import logging
from django.http import JsonResponse, HttpResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 1. Define pure views first
def home(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    compute_url = f"{base_url}/api/v1/compute?x=5&y=10"

    html = f"""
    <html>
        <body style="font-family: sans-serif; padding: 50px; background: #0f172a; color: #f8fafc;">
            <h2>🛰️ GlobalHost Django API Node Active</h2>
            <p><strong>Status:</strong> HEALTHY</p>
            <p><strong>Click to test API Endpoint:</strong> <a style="color: #38bdf8;" href="{compute_url}" target="_blank">{compute_url}</a></p>
        </body>
    </html>
    """
    return HttpResponse(html)

def compute_metrics(request):
    try:
        x = float(request.GET.get('x', 1.0))
        y = float(request.GET.get('y', 1.0))
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid numeric inputs"}, status=400)

    result = (x + y)
    return JsonResponse({
        "status": "success",
        "payload": {"input_x": x, "input_y": y, "computed_result": result}
    })

# 2. Wire Routing to an explicit array name
from django.urls import path
URLS = [
    path("", home),
    path("api/v1/compute", compute_metrics),
]

# 3. Explicitly declare Global Settings for Django Module Loader
DEBUG = True
SECRET_KEY = "globalhost-local-dev-key"
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = __name__
# Tell Django explicitly to look for 'URLS' instead of parsing __name__ strings
ROOT_URLCONF_VARIABLE = "URLS"
urlpatterns = URLS

if __name__ == "__main__":
    from globalhost import GlobalHostApp
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", __name__)

    gh = GlobalHostApp()
    gh.launch(framework="django", app=__file__, port=8000)
