from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.panel_view, name="panel"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("<int:convocatoria_pk>/procesar/", views.procesar_view, name="procesar"),
    path("<int:convocatoria_pk>/ranking/", views.ranking_view, name="ranking"),
    path("<int:convocatoria_pk>/excel/", views.exportar_excel_view, name="excel"),
    path("<int:convocatoria_pk>/pdf/", views.exportar_pdf_view, name="pdf"),
]
