from django.contrib import admin




from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),  # URLs de tu app
    path('accounts/', include('allauth.urls')),  # URLs de autenticación con Gmail y Django
]



