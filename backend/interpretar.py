import json
from groq import Groq
import os
from datetime import datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str):
    prompt = f"""
Eres un asistente de inventario. Responde SOLO con JSON válido.

REGLAS IMPORTANTES:
- NO escribas nada fuera del JSON.
- NO uses comentarios.
- NO expliques nada.
- SOLO JSON puro.
- Si el usuario no menciona la fecha de ingreso, asígnala automáticamente con la fecha actual del sistema en formato YYYY-MM-DD.
- Si el usuario sí menciona la fecha de ingreso, respétala.
- Si el usuario dice explícitamente "Por definir" en fecha_ingreso, déjala como "Por definir".
- Para los demás campos no mencionados, usa "Por definir".
- Si el usuario quiere editar un campo, usa la acción "editar".
- Si el usuario está eligiendo entre varias opciones, usa la acción "seleccionar".
- En consultas como "cuánto queda de X", SIEMPRE incluye el campo "producto".

ACCIONES DISPONIBLES:
- agregar
- eliminar
- consultar
- editar
- consultar_tipo
- consultar_marca
- consultar_caducidad
- consultar_ingreso
- seleccionar

CAMPOS DISPONIBLES:
- producto
- cantidad
- tipo
- marca
- fecha_ingreso
- fecha_caducidad
- campo
- valor
- dias
- opcion
- accion_original

Ahora interpreta este mensaje:
{mensaje}
"""

    try:
        respuesta = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        contenido = respuesta.choices[0].message.content.strip()

        inicio = contenido.find("{")
        fin = contenido.rfind("}")

        if inicio == -1 or fin == -1:
            raise ValueError("No se encontró JSON válido")

        contenido = contenido[inicio:fin+1]

        accion_json = json.loads(contenido)

        if "accion" not in accion_json:
            accion_json["accion"] = "error"

        if accion_json["accion"].startswith("consultar") and "producto" not in accion_json:
            accion_json["producto"] = "Por definir"

        if accion_json.get("fecha_ingreso") in [None, "", "-", "por definir", "Por definir"]:
            accion_json["fecha_ingreso"] = datetime.now().strftime("%Y-%m-%d")

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
