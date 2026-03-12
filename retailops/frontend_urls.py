from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponse
import os

class ReactAppView(TemplateView):
    def get(self, request, *args, **kwargs):
        if settings.DEBUG:
            return HttpResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>RetailOps - Development</title>
                </head>
                <body>
                    <h2>Development Mode</h2>
                    <p>Please run the Vite dev server:</p>
                    <pre>cd frontend && npm run dev</pre>
                    <p>Then access the app at: <a href="http://localhost:3000">http://localhost:3000</a></p>
                </body>
                </html>
                """,
                content_type='text/html'
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

