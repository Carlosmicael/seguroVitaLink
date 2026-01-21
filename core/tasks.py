# apps/abogado_app/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Notificaciones
import logging
import pusher
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
logger = logging.getLogger(__name__)



pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)





@shared_task(bind=True)
def ejecutar_recordatorio(self):
    try:
        print("Llegó a ejecutar_recordatorio!")
        task_id = self.request.id
        print(f"Ejecutando tarea con ID: {task_id}")
        recordatorio = Notificaciones.objects.get(not_celery_task_id=task_id)


        enviar_recordatorio(recordatorio.not_codcli.user,recordatorio.not_mensaje,recordatorio.not_fecha_proceso)
        pusher_client.trigger(f"private-user-{recordatorio.not_codcli.user.id}", 'my-event', {'message': f'Hola, usuario {recordatorio.not_codcli.user.id}! Tienes una nueva notificación.'})
        
        recordatorio.not_read = True
        recordatorio.not_estado = True
        recordatorio.save()
        print(f"Mensaje del recordatorio {recordatorio.not_id}: {recordatorio.not_mensaje}")
        print(f"Recordatorio {recordatorio.not_id} su parametro se actualizo a True ({recordatorio.not_read}).")

    except Notificaciones.DoesNotExist:
        print(f"No se encontró un recordatorio para la tarea con ID: {task_id}. Pudo haber sido borrado manualmente.")







def enviar_recordatorio(user,mensaje,fecha):
        subject = 'Recordatorio vitaLink'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]
        html_message = render_to_string('recordatorio.html', {'usuario': user,'mensaje': mensaje,'fecha': fecha})
        try:
            send_mail(subject, '', from_email, to_email, html_message=html_message)
            logging.warning(f"Recordatorio enviado a {user.email}")
        except Exception as e:
            logging.warning(f"Error al enviar el recordatorio: {e}")














