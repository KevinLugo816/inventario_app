import json
from groq import Groq
import os
from datetime import datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str, contexto: str = ""):
    """
    mensaje  = mensaje actual del usuario
    contexto = última respuesta del backend (puede ser vacío)
    """

    hoy = datetime.now().strftime("%d-%m-%Y")

    def singularizar(p):
        p = p.lower().strip()
        if p.endswith("es"):
            return p[:-2]
        if p.endswith("s"):
            return p[:-1]
        return p

    prompt = f"""
Eres Bell, un asistente experto en inventario.
Responde SOLO con JSON válido, sin texto adicional.

CONTEXTO DE LA CONVERSACIÓN:
"{contexto}"

MENSAJE DEL USUARIO:
"{mensaje}"

REGLAS GENERALES:
- SOLO JSON puro.
- Si falta un campo, usa "Por definir".
- Si falta fecha_ingreso, usa la fecha actual en DD-MM-YYYY.
- Convierte plurales a singular.
- Prioridad: agregar > editar > eliminar > consultar > seleccionar.

REGLAS PARA SELECCIONAR:
- Si el contexto indica que el sistema pidió especificar lote, marca o tipo,
  entonces cualquier respuesta corta del usuario debe interpretarse como acción = seleccionar.
- Respuestas cortas incluyen:
  "marca X", "tipo X", "lote X", "2", "el más nuevo", "el más viejo",
  "el que vence primero", "el que vence después".
- En selección:
  - "producto": null
  - "opcion": mensaje exacto del usuario

REGLAS PARA CONSULTAR:
- "cuánto queda", "cuánto hay", "qué cantidad" → consultar
- Consultas SIEMPRE incluyen "producto".

REGLAS PARA EDITAR:
- "cambia", "modifica", "actualiza", "edita" → editar
- En edición:
  - "campo": campo a editar
  - "valor": nuevo valor

REGLAS PARA AGREGAR:
- "agrega X producto" → agregar
- "agrega X más" o "ponle X más" → editar cantidad

ACCIONES PERMITIDAS:
- agregar
- eliminar
- consultar
- editar
- consultar_tipo
- consultar_marca
- consultar_caducidad
- consultar_ingreso
- seleccionar

CAMPOS PERMITIDOS:
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

Interpreta el mensaje del usuario según las reglas anteriores.
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

        accion_json = json.loads(contenido[inicio:fin+1])

        if "producto" in accion_json and accion_json["producto"]:
            accion_json["producto"] = singularizar(accion_json["producto"])

        fecha = accion_json.get("fecha_ingreso", "").strip()
        if fecha.lower() in ["", "por definir", "-", "none", "null"]:
            accion_json["fecha_ingreso"] = hoy
        else:
            try:
                if "-" in fecha and len(fecha.split("-")[0]) == 4:
                    y, m, d = fecha.split("-")
                    accion_json["fecha_ingreso"] = f"{d}-{m}-{y}"
            except:
                accion_json["fecha_ingreso"] = hoy

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
