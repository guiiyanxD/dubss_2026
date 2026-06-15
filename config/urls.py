from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("acceso/", include("apps.acceso.urls", namespace="acceso")),
    path("usuarios/", include("apps.usuarios.urls", namespace="usuarios")),
    path("convocatorias/", include("apps.convocatorias.urls", namespace="convocatorias")),
    path("", RedirectView.as_view(pattern_name="acceso:inicio", permanent=False)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
