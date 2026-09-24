# asistente_panaderia.py
# Asistente del sistema de ventas de Panadería Los Andes con Groq (gratis) + reportes por WhatsApp
import os
import sys
from datetime import datetime
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from enviar_whatsapp import enviar_whatsapp

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    sys.exit("❌ Falta GROQ_API_KEY. Crea el archivo .env (copia .env.example) y coloca tu key de Groq.")

# Groq es compatible con la librería de OpenAI: solo cambiamos base_url y la key
client = OpenAI(api_key=API_KEY, base_url="https://api.groq.com/openai/v1")
MODELO = "openai/gpt-oss-120b"

CATALOGO = """
Productos y precios (en soles):
- Pan francés: S/ 0.30 c/u
- Pan de yema: S/ 0.50 c/u
- Empanada: S/ 4.50 c/u
- Torta de chocolate: S/ 45.00 c/u
"""

INSTRUCCIONES = f"""
Eres el ASISTENTE DEL SISTEMA DE VENTAS de la Panadería Los Andes (Perú).
Trabajas junto al vendedor en caja: registras pedidos, calculas totales y
das información útil para el negocio.
{CATALOGO}
Tus funciones:
1. Registrar cada pedido: producto, cantidad, subtotal y TOTAL en soles (2 decimales).
2. Confirmar el pedido antes de darlo por vendido ("Venta registrada ✅").
3. Si piden algo que no está en el catálogo, indícalo y sugiere una alternativa.
4. Sugerir ventas complementarias cuando tenga sentido (ej.: pan + empanada, torta para celebraciones).
5. Emitir NOTIFICACIONES útiles para el rubro con el prefijo "🔔 AVISO:", por ejemplo:
   - pedidos grandes (más de S/ 50 o más de 50 panes) que requieren preparación anticipada,
   - pedidos de tortas (recordar tiempo de elaboración),
   - productos con alta demanda en la sesión.
6. Si el vendedor pregunta por ventas acumuladas, resume lo vendido en la conversación.
Responde de forma breve, clara y amable. No inventes productos ni precios.
Usa texto plano (se muestra en consola): sin tablas ni markdown (**, |, #).
"""

INSTRUCCIONES_REPORTE = f"""
Eres el módulo de reportes del sistema de ventas de la Panadería Los Andes.
{CATALOGO}
A partir de la conversación, genera un REPORTE DE VENTAS breve (máximo 12 líneas) con:
- Ventas confirmadas: producto, cantidad y subtotal.
- TOTAL VENDIDO en soles y número de pedidos.
- Producto más vendido.
- Avisos para el negocio (pedidos grandes, tortas por preparar, productos a reponer).
- 1 recomendación corta para mejorar las ventas.
Si no hubo compras, escribe: 'No se concretó ninguna venta' y una recomendación.
Texto plano, sin tablas ni markdown (se enviará por WhatsApp).
"""


def preguntar(instrucciones, entrada):
    """Llama al modelo y devuelve el texto; None si hubo error."""
    try:
        respuesta = client.responses.create(
            model=MODELO,
            instructions=instrucciones,
            input=entrada,
        )
        return respuesta.output_text.strip()
    except OpenAIError as e:
        print(f"❌ Error al consultar el modelo: {e}")
        return None


def generar_reporte(historial):
    """Pide al modelo un reporte de ventas a partir de la conversación."""
    conversacion = "\n".join(f"{m['role']}: {m['content']}" for m in historial)
    return preguntar(INSTRUCCIONES_REPORTE, conversacion)


def enviar_reporte(historial):
    """Genera el reporte, lo muestra y lo envía por WhatsApp."""
    if not historial:
        print("No hubo conversación, no se generó reporte.")
        return

    print("\nGenerando reporte de ventas...")
    reporte = generar_reporte(historial)
    if not reporte:
        print("❌ No se pudo generar el reporte.")
        return

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    mensaje = f"REPORTE DE VENTAS - Panadería Los Andes\nFecha: {fecha}\n\n{reporte}"
    print("\n" + mensaje)

    print("\nEnviando por WhatsApp...")
    if enviar_whatsapp(mensaje):
        print("✅ Se realizó el reporte de ventas y se envió con éxito.\n")
    else:
        print("❌ El reporte se generó, pero no se pudo enviar por WhatsApp.\n")


def main():
    historial = []
    print("Panadería Los Andes - Asistente del sistema de ventas")
    print("Comandos: 'reporte' = enviar reporte y seguir | 'salir' = enviar reporte final y terminar\n")

    while True:
        try:
            texto = input("Cliente: ").strip()
        except (EOFError, KeyboardInterrupt):
            texto = "salir"

        comando = texto.lower()
        if comando == "reporte":
            enviar_reporte(historial)
            continue
        if comando == "salir":
            enviar_reporte(historial)
            break
        if not texto:
            continue

        historial.append({"role": "user", "content": texto})
        respuesta = preguntar(INSTRUCCIONES, historial)
        if respuesta is None:
            historial.pop()  # no guardar un mensaje sin respuesta
            continue

        print("Asistente:", respuesta, "\n")
        historial.append({"role": "assistant", "content": respuesta})


if __name__ == "__main__":
    main()
