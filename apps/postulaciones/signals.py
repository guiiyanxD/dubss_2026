from django.dispatch import Signal

postulacion_enviada = Signal()  # kwargs: postulacion
identidad_verificada = Signal()  # kwargs: postulacion, aprobada
documentacion_procesada = Signal()  # kwargs: postulacion, aprobada
resultado_adjudicacion = Signal()  # kwargs: postulacion
