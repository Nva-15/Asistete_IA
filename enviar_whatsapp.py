# enviar_whatsapp.py
# Envía un mensaje de WhatsApp al NUMERO_DOCENTE.
#   - Con Green-API (GREEN_API_ID_INSTANCE y GREEN_API_TOKEN en .env / secrets):
#     envía por internet desde tu WhatsApp vinculado, funciona en Streamlit Cloud.
#   - Sin Green-API: usa pywhatkit, que abre WhatsApp Web (solo en tu PC).
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def _numero_destino():
    return (os.getenv("NUMERO_DOCENTE") or "").strip()  # ejemplo: +51900000000


def _enviar_green_api(numero, mensaje):
    id_instancia = os.getenv("GREEN_API_ID_INSTANCE")
    token = os.getenv("GREEN_API_TOKEN")
    base = os.getenv("GREEN_API_URL", "https://api.green-api.com").rstrip("/")
    url = f"{base}/waInstance{id_instancia}/sendMessage/{token}"
    chat_id = f"{numero.lstrip('+')}@c.us"
    r = requests.post(url, json={"chatId": chat_id, "message": mensaje}, timeout=30)
    if r.status_code == 200 and "idMessage" in r.text:
        return True, "Enviado por Green-API"
    return False, f"Green-API respondió {r.status_code}: {r.text[:200]}"


def _enviar_pywhatkit(numero, mensaje):
    # Import aquí: pywhatkit solo funciona en una PC con navegador (no en la nube)
    import pywhatkit

    pywhatkit.sendwhatmsg_instantly(
        phone_no=numero,
        message=mensaje,
        wait_time=20,     # segundos que espera a que cargue WhatsApp Web
        tab_close=True,   # cierra la pestaña al terminar
        close_time=5,
    )
    return True, "Enviado por WhatsApp Web"


def enviar_whatsapp_detalle(mensaje: str):
    """Envía el mensaje al NUMERO_DOCENTE. Devuelve (ok, detalle)."""
    numero = _numero_destino()
    if not numero.startswith("+"):
        return False, "Define NUMERO_DOCENTE con código de país (ej. +51900000000)."
    try:
        if os.getenv("GREEN_API_ID_INSTANCE") and os.getenv("GREEN_API_TOKEN"):
            return _enviar_green_api(numero, mensaje)
        return _enviar_pywhatkit(numero, mensaje)
    except Exception as e:
        return False, (f"No se pudo enviar ({e}). En la nube configura "
                       "GREEN_API_ID_INSTANCE y GREEN_API_TOKEN en los Secrets.")


def enviar_whatsapp(mensaje: str) -> bool:
    """Devuelve True si se envió, False si hubo error."""
    ok, detalle = enviar_whatsapp_detalle(mensaje)
    if not ok:
        print(detalle)
    return ok
