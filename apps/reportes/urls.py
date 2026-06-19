from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.panel_view, name="panel"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("ia/resumen/", views.resumen_ia_solicitar_view, name="resumen_ia_solicitar"),
    path(
        "ia/resumen/<int:resumen_pk>/estado/",
        views.resumen_ia_estado_view,
        name="resumen_ia_estado",
    ),
    path(
        "ia/resumen/<int:resumen_pk>/pdf/",
        views.resumen_ia_exportar_pdf_view,
        name="resumen_ia_pdf",
    ),
    path("ia/chat/", views.chat_lista_view, name="chat_lista"),
    path("ia/chat/<int:conversacion_pk>/", views.chat_detalle_view, name="chat_detalle"),
    path("ia/chat/<int:conversacion_pk>/estado/", views.chat_estado_view, name="chat_estado"),
    path("<int:convocatoria_pk>/procesar/", views.procesar_view, name="procesar"),
    path("<int:convocatoria_pk>/ranking/", views.ranking_view, name="ranking"),
    path("<int:convocatoria_pk>/excel/", views.exportar_excel_view, name="excel"),
    path("<int:convocatoria_pk>/pdf/", views.exportar_pdf_view, name="pdf"),
]
