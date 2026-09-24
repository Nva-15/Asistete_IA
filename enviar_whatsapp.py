# enviar_whatsapp.py
# Envía un mensaje de WhatsApp GRATIS usando tu propio WhatsApp Web.
import os
from dotenv import load_dotenv

load_dotenv()
NUMERO = os.getenv("NUMERO_DOCENTE")  # ejemplo: +51987105426


def enviar_whatsapp(mensaje: str) -> bool:
    """Devuelve True si se envió, False si hubo error."""
    if not NUMERO or not NUMERO.startswith("+"):
        print("Error: define NUMERO_DOCENTE en .env con código de país (ej. +51987105426).")
        return False
    try:
        # Import aquí: si pywhatkit falla, el asistente sigue funcionando
        import pywhatkit

        pywhatkit.sendwhatmsg_instantly(
            phone_no=NUMERO,
            message=mensaje,
            wait_time=20,     # segundos que espera a que cargue WhatsApp Web
            tab_close=True,   # cierra la pestaña al terminar
            close_time=5,
        )
        return True
    except Exception as e:
        print(f"Error al enviar WhatsApp: {e}")
        return False
