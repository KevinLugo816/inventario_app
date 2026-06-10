import json
from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str):
    prompt = """
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
""" + mensaje

    try:
        respuesta = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        contenido = respuesta.choices[0].message.content.strip()

        # Asegurar que sea JSON válido
        if not contenido.startswith("{"):
            inicio = contenido.find("{")
            fin = contenido.rfind("}")
            if inicio != -1 and fin != -1:
                contenido = contenido[inicio:fin+1]

        accion_json = json.loads(contenido)

        if "accion" not in accion_json:
            return {"accion": "error", "producto": "", "cantidad": 0}

        if accion_json["accion"].startswith("consultar") and "producto" not in accion_json:
            accion_json["producto"] = "Por definir"

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
