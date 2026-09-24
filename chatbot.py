import os
from groq import Groq

# OBTENCIÓN DE API KEY (con fallback)
def _obtener_api_key():
    # 1. Streamlit Cloud
    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        # En local sin streamlit activo, seguir al fallback
        pass

    # 2. .env local
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    return os.environ.get("GROQ_API_KEY", "")

# CLIENTE GROQ (lazy singleton)
_client = None


def _get_client():
    """Crea el cliente Groq bajo demanda (una sola vez)."""
    global _client
    if _client is None:
        api_key = _obtener_api_key()
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY no está configurada. "
                "Agrega la clave en .streamlit/secrets.toml (local) o "
                "en Settings → Secrets de Streamlit Cloud."
            )
        _client = Groq(api_key=api_key)
    return _client

# CONSULTA A GROQ
def consultar_groq(messages, temperature=0.3, max_tokens=1024):
    """Envía mensajes a Groq usando openai/gpt-oss-120b."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="low"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Error] {str(e)}"


def chat_con_contexto(prompt_sistema, historial, pregunta_usuario,
                       temperature=0.3, max_tokens=1024):
    """Construye el contexto completo y consulta a Groq."""
    mensajes = [{"role": "system", "content": prompt_sistema}]
    mensajes.extend(historial)
    mensajes.append({"role": "user", "content": pregunta_usuario})
    return consultar_groq(mensajes, temperature, max_tokens)

# DIAGNÓSTICO
def api_key_configurada():
    """Devuelve True si hay una API Key disponible."""
    try:
        return bool(_obtener_api_key())
    except Exception:
        return False


if __name__ == "__main__":
    # Prueba rápida desde terminal
    print("API Key configurada:", api_key_configurada())
    if api_key_configurada():
        respuesta = consultar_groq([
            {"role": "user", "content": "Responde solo: OK"}
        ])
        print("Respuesta:", respuesta)