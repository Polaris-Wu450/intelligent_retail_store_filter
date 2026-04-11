from django.urls import path, include

urlpatterns = [
    path('api/', include('retailops.api.urls')),
    path('', include('retailops.frontend_urls')),
]

