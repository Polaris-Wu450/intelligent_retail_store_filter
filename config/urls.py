from django.urls import path, include

urlpatterns = [
    path('', include('django_prometheus.urls')),  # exposes /metrics
    path('api/', include('retailops.api.urls')),
    path('', include('retailops.frontend_urls')),
]

