import ollama
import json

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

EJEMPLOS:

Usuario: "agrega 5 arroz marca Polar"
Respuesta:
{
    "accion": "agregar",
    "producto": "arroz",
    "cantidad": 5,
    "tipo": "Por definir",
    "marca": "Polar",
    "fecha_ingreso": "Por definir",
    "fecha_caducidad": "Por definir"
}

Usuario: "cuánto queda de arroz"
Respuesta:
{
    "accion": "consultar",
    "producto": "arroz"
}

Usuario: "cambia la fecha de caducidad de la leche a 2026-07-01"
Respuesta:
{
    "accion": "editar",
    "producto": "leche",
    "campo": "fecha_caducidad",
    "valor": "2026-07-01"
}

Ahora interpreta este mensaje:
""" + mensaje

    try:
        respuesta = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        contenido = respuesta["message"]["content"].strip()

        if not contenido.startswith("{"):
            inicio = contenido.find("{")
            fin = contenido.rfind("}")
            if inicio != -1 and fin != -1:
                contenido = contenido[inicio:fin+1]

        accion_json = json.loads(contenido)

        if "accion" not in accion_json:
            return {"accion": "error", "producto": "", "cantidad": 0}

        # Si es consulta, aseguramos que tenga producto
        if accion_json["accion"].startswith("consultar") and "producto" not in accion_json:
            accion_json["producto"] = "Por definir"

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
