# enviar_whatsapp.py
# Envía un mensaje de WhatsApp automáticamente mediante una API (funciona en la nube,
# p. ej. Streamlit Cloud, sin abrir WhatsApp Web).
#
# Proveedores soportados (se usa el primero que esté configurado en .env / secrets):
#   1. Green-API  -> GREEN_API_ID_INSTANCE, GREEN_API_TOKEN (opcional GREEN_API_URL)
#   2. Twilio     -> TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
import os
import requests
from dotenv import load_dotenv

load_dotenv()

LIMITE_TWILIO = 1500  # Twilio acepta hasta 1600 caracteres por mensaje


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


def _partir(mensaje, limite):
    """Divide un texto largo en trozos respetando los saltos de línea."""
    partes, actual = [], ""
    for linea in mensaje.splitlines(keepends=True):
        while len(linea) > limite:
            partes.append(linea[:limite])
            linea = linea[limite:]
        if len(actual) + len(linea) > limite:
            partes.append(actual)
            actual = ""
        actual += linea
    if actual.strip():
        partes.append(actual)
    return partes


def _enviar_twilio(numero, mensaje):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    origen = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")  # número del sandbox
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    for parte in _partir(mensaje, LIMITE_TWILIO):
        r = requests.post(
            url,
            auth=(sid, token),
            data={
                "From": f"whatsapp:{origen.removeprefix('whatsapp:')}",
                "To": f"whatsapp:{numero}",
                "Body": parte,
            },
            timeout=30,
        )
        if r.status_code not in (200, 201):
            return False, f"Twilio respondió {r.status_code}: {r.text[:200]}"
    return True, "Enviado por Twilio"


def enviar_whatsapp_detalle(mensaje: str):
    """Envía el mensaje al NUMERO_DOCENTE. Devuelve (ok, detalle)."""
    numero = _numero_destino()
    if not numero.startswith("+"):
        return False, "Define NUMERO_DOCENTE con código de país (ej. +51900000000)."
    try:
        if os.getenv("GREEN_API_ID_INSTANCE") and os.getenv("GREEN_API_TOKEN"):
            return _enviar_green_api(numero, mensaje)
        if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
            return _enviar_twilio(numero, mensaje)
        return False, ("No hay API de WhatsApp configurada. Define GREEN_API_ID_INSTANCE "
                       "y GREEN_API_TOKEN (o las variables de Twilio) en .env / secrets.")
    except Exception as e:
        return False, f"Error al enviar WhatsApp: {e}"


def enviar_whatsapp(mensaje: str) -> bool:
    """Devuelve True si se envió, False si hubo error."""
    ok, detalle = enviar_whatsapp_detalle(mensaje)
    if not ok:
        print(detalle)
    return ok
