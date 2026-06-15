from django.dispatch import Signal

# Enviada cuando una convocatoria pasa al estado CERRADA.
# kwargs: convocatoria (instancia de Convocatoria)
convocatoria_cerrada = Signal()
