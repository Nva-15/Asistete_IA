import os
from datetime import datetime
from chatbot import consultar_groq
from shot_prompts import SHOT_PROMPTS, DATOS_VENTAS_PRUEBA, PREGUNTA

PRUEBAS_DIR = "pruebas"
os.makedirs(PRUEBAS_DIR, exist_ok=True)

TEMPERATURE = 0.3
MAX_TOKENS = 400

def _guardar_evidencia(clave, nombre, respuesta):
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ruta = f"{PRUEBAS_DIR}/{clave}_{ts}.md"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"# {nombre}\n\n")
        f.write(f"**Pregunta:** {PREGUNTA}\n\n")
        f.write(f"**Datos:**\n```\n{DATOS_VENTAS_PRUEBA}\n```\n\n")
        f.write(f"**Respuesta de Groq:**\n\n{respuesta}\n")
    return ruta

def ejecutar_tecnica(clave):
    """Ejecuta una sola técnica (zero_shot/one_shot/few_shot) contra Groq."""
    cfg = SHOT_PROMPTS[clave]
    respuesta = consultar_groq(
        messages=[
            {"role": "system", "content": cfg["sistema"]},
            {"role": "user", "content": cfg["usuario"]},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    _guardar_evidencia(clave, cfg["nombre"], respuesta)
    return respuesta

def ejecutar_comparacion():
    """Ejecuta las 3 técnicas con los mismos datos y pregunta."""
    return {
        clave: {
            "nombre": SHOT_PROMPTS[clave]["nombre"],
            "respuesta": ejecutar_tecnica(clave),
        }
        for clave in ("zero_shot", "one_shot", "few_shot")
    }
