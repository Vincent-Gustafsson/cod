from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/register/', include('dj_rest_auth.registration.urls')),

    path('api/', include('users.urls')),
    path('api/', include('articles.urls')),
    path('api/', include('moderation.urls')),
    path('api/', include('notifications.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
