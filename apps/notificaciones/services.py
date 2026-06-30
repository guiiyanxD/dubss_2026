from .models import Notificacion


class NotificacionService:

    @staticmethod
    def enviar_notificacion(*, usuario, asunto, cuerpo):
        """Crea un registro de notificación y encola el envío de email vía Celery.

        Args:
            usuario: Instancia de Usuario destinatario.
            asunto: Asunto del email.
            cuerpo: Cuerpo del email (texto plano).

        Returns:
            La instancia de Notificacion creada.
        """
        notif = Notificacion.objects.create(usuario=usuario, asunto=asunto, cuerpo=cuerpo)
        from .tasks import tarea_enviar_email

        tarea_enviar_email.delay(notif.pk)
        return notif

    @staticmethod
    def notificar_postulacion_enviada(*, postulacion):
        """Notifica al estudiante que su postulación fue recibida."""
        return NotificacionService.enviar_notificacion(
            usuario=postulacion.estudiante,
            asunto=f"Postulación recibida — {postulacion.convocatoria.nombre}",
            cuerpo=(
                f"Hola {postulacion.estudiante.get_full_name()},\n\n"
                f"Tu postulación para la convocatoria «{postulacion.convocatoria.nombre}» "
                f"(beca: {postulacion.beca.nombre}) fue recibida correctamente.\n\n"
                "Próximamente un operador verificará tu identidad de forma presencial.\n\n"
                "Sistema de Becas Universitarias"
            ),
        )

    @staticmethod
    def notificar_identidad_verificada(*, postulacion, aprobada):
        """Notifica al estudiante el resultado de la verificación de identidad."""
        if aprobada:
            tiene_docs = postulacion.documentos.exists()
            if tiene_docs:
                resultado = "aprobada. Deberás presentar tu documentación para continuar el proceso."
            else:
                resultado = "aprobada y tu postulación pasa a estado Aprobada."
        else:
            resultado = (
                f"rechazada. Motivo: {postulacion.observaciones_identidad or 'no especificado'}."
            )

        return NotificacionService.enviar_notificacion(
            usuario=postulacion.estudiante,
            asunto=f"Verificación de identidad — {postulacion.convocatoria.nombre}",
            cuerpo=(
                f"Hola {postulacion.estudiante.get_full_name()},\n\n"
                f"Tu identidad en la convocatoria «{postulacion.convocatoria.nombre}» fue {resultado}\n\n"
                "Sistema de Becas Universitarias"
            ),
        )

    @staticmethod
    def notificar_documentacion_procesada(*, postulacion, aprobada):
        """Notifica al estudiante el resultado de la validación documental."""
        if aprobada:
            resultado = "toda la documentación presentada fue aprobada. Tu postulación está Aprobada."
        else:
            resultado = "uno o más documentos fueron rechazados. Tu postulación no puede continuar."

        return NotificacionService.enviar_notificacion(
            usuario=postulacion.estudiante,
            asunto=f"Resultado de documentación — {postulacion.convocatoria.nombre}",
            cuerpo=(
                f"Hola {postulacion.estudiante.get_full_name()},\n\n"
                f"Respecto a tu postulación en «{postulacion.convocatoria.nombre}»: {resultado}\n\n"
                "Sistema de Becas Universitarias"
            ),
        )

    @staticmethod
    def notificar_resultado_adjudicacion(*, postulacion):
        """Notifica al estudiante el resultado final de adjudicación."""
        estado = postulacion.get_estado_display()
        if postulacion.estado == "ADJUDICADA":
            mensaje = f"¡Felicitaciones! Fuiste adjudicado/a en la beca «{postulacion.beca.nombre}»."
        elif postulacion.estado == "LISTA_ESPERA":
            mensaje = (
                f"Quedaste en lista de espera para la beca «{postulacion.beca.nombre}». "
                "Te notificaremos si se libera un cupo."
            )
        else:
            mensaje = (
                f"Lamentablemente no fuiste adjudicado/a en la beca «{postulacion.beca.nombre}» "
                f"(estado: {estado})."
            )

        return NotificacionService.enviar_notificacion(
            usuario=postulacion.estudiante,
            asunto=f"Resultado de adjudicación — {postulacion.convocatoria.nombre}",
            cuerpo=(
                f"Hola {postulacion.estudiante.get_full_name()},\n\n"
                f"{mensaje}\n\n"
                "Sistema de Becas Universitarias"
            ),
        )
