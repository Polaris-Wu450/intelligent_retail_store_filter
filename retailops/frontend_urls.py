from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponse
import os

# DEBUG: never auto-redirect away from :8000 — users need a stable API origin and may use Vite on another port.
_DEV_STUB_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RetailOps - Development</title>
</head>
<body style="font-family: system-ui; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5;">
    <h2>RetailOps — Django on :8000</h2>
    <p>This URL is the <strong>API</strong> (e.g. <code>/api/...</code>). There is no React dev server here.</p>

    <h3 style="margin-top:1.5rem;">Your usual frontend (hot reload)</h3>
    <pre style="background:#f4f4f5;padding:1rem;border-radius:8px;">cd frontend && npm run dev</pre>
    <p>Open whatever URL the terminal prints (often <a href="{vite_url}">{vite_url}</a> — if Vite uses another port, use that).</p>
    <p style="color:#666;font-size:0.9rem;">Optional: set <code>FRONTEND_DEV_URL</code> in <code>.env</code> so the link above matches your Vite port (e.g. <code>http://localhost:3002</code>).</p>

    <h3 style="margin-top:1.5rem;">Docker packaged UI (production build)</h3>
    <p>If you run <code>docker compose up</code> with the <code>frontend</code> service, the built app is at
    <a href="http://localhost:3000">http://localhost:3000</a> — that is <strong>not</strong> the same as <code>npm run dev</code> (no HMR).</p>
</body>
</html>
"""


class ReactAppView(TemplateView):
    def get(self, request, *args, **kwargs):
        if settings.DEBUG:
            vite_base = os.getenv('FRONTEND_DEV_URL', 'http://localhost:3000').rstrip('/')
            return HttpResponse(
                _DEV_STUB_HTML.format(vite_url=vite_base + '/'),
                content_type='text/html',
            )
        else:
            index_path = os.path.join(settings.BASE_DIR, 'static', 'dist', 'index.html')
            try:
                with open(index_path, 'r') as f:
                    return HttpResponse(f.read(), content_type='text/html')
            except FileNotFoundError:
                return HttpResponse(
                    "Production build not found. Run: cd frontend && npm run build",
                    status=500
                )

urlpatterns = [
    re_path(r'^.*$', ReactAppView.as_view(), name='index'),
]

