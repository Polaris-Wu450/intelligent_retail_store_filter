from django.urls import path, include

urlpatterns = [
    path('api/', include('retailops.urls')),
    path('', include('retailops.frontend_urls')),
]

