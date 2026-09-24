import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from dotenv import load_dotenv
from database import obtener_notificaciones_no_leidas

load_dotenv()


def notificar_email(asunto, mensaje, destinatario):
    """Envía notificación por correo (opcional)."""
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    if not remitente or not password:
        return False

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.attach(MIMEText(mensaje, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False


def notificar_telegram(mensaje):
    """Envía notificación por Telegram (opcional)."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": mensaje})
        return r.status_code == 200
    except Exception:
        return False


def obtener_pendientes():
    """Devuelve las notificaciones no leídas para mostrar en Streamlit."""
    return obtener_notificaciones_no_leidas()

def _texto_plano(mensaje):
    """Quita markdown (**, #, tablas) para que el mensaje se lea bien en WhatsApp."""
    lineas = []
    for linea in mensaje.splitlines():
        l = linea.strip()
        if set(l) <= set("|-: "):  # separador de tabla markdown
            if l:
                continue
        if l.startswith("|"):
            l = " - ".join(c.strip() for c in l.strip("|").split("|"))
        l = l.replace("**", "").replace("__", "").lstrip("#").strip()
        lineas.append(l)
    return "\n".join(lineas).strip()


def notificar_whatsapp(mensaje):
    """Envía notificación por WhatsApp Web (opcional, requiere NUMERO_DOCENTE)."""
    if os.getenv("WHATSAPP_ACTIVO", "1") == "0" or not os.getenv("NUMERO_DOCENTE"):
        return False
    from enviar_whatsapp import enviar_whatsapp
    return enviar_whatsapp(_texto_plano(mensaje))


def _con_encabezado(titulo, mensaje, usuario=None):
    from datetime import datetime
    responsable = f"Técnico en turno: {usuario}\n" if usuario else ""
    return (f"{titulo} - Panadería Los Andes\n"
            f"{responsable}"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n{mensaje}")


def enviar_por_whatsapp(titulo, mensaje, usuario=None):
    """Envía un reporte solo por WhatsApp. Devuelve (ok, detalle)."""
    if os.getenv("WHATSAPP_ACTIVO", "1") == "0":
        return False, "El envío por WhatsApp está desactivado (WHATSAPP_ACTIVO=0 en .env)."
    if not os.getenv("NUMERO_DOCENTE"):
        return False, "Falta NUMERO_DOCENTE en el archivo .env."
    if notificar_whatsapp(_con_encabezado(titulo, mensaje, usuario)):
        return True, "Enviado"
    return False, "WhatsApp Web no pudo enviar el mensaje (revisa la consola)."


def enviar_notificacion_externa(titulo, mensaje, usuario=None):
    """
    Envía un reporte/alerta por todos los canales configurados en .env
    (WhatsApp, Telegram y correo). Devuelve la lista de canales que funcionaron.
    """
    texto = _con_encabezado(titulo, mensaje, usuario)
    canales = []
    if notificar_whatsapp(texto):
        canales.append("WhatsApp")
    if notificar_telegram(_texto_plano(texto)):
        canales.append("Telegram")
    destinatario = os.getenv("EMAIL_DESTINO")
    if destinatario and notificar_email(titulo, _texto_plano(texto), destinatario):
        canales.append("Correo")
    return canales
