import json
from groq import Groq
import os
from datetime import datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str):
    hoy = datetime.now().strftime("%d-%m-%Y")

    prompt = f"""
Eres Bell, un asistente experto en gestión de inventario.
Tu única salida debe ser SIEMPRE un JSON válido, sin texto adicional.

REGLAS ESTRICTAS:
- NO escribas nada fuera del JSON.
- NO uses comentarios.
- NO expliques nada.
- SOLO JSON puro.
- Si falta un campo, usa "Por definir".
- Si falta fecha_ingreso, usa la fecha actual del sistema en formato DD-MM-YYYY.
- Si el usuario dice explícitamente "Por definir", respétalo.
- Si el usuario corrige algo ("quise decir", "me equivoqué"), usa acción "editar".
- Si el usuario compara, pregunta o consulta, usa acción "consultar".
- Si el usuario pregunta por cantidades, SIEMPRE incluye "producto".
- Si el usuario menciona varios productos, responde SOLO sobre el primero.
- Si el usuario pide varias acciones, responde SOLO la más importante.
- Si el usuario está eligiendo entre opciones, usa acción "seleccionar".
- Si el usuario dice "agrega X más", interpreta como editar cantidad.
- Si el usuario dice "cuánto queda", "cuánto hay", "cuántos quedan", es acción consultar.

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

Ahora interpreta este mensaje del usuario:
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

        acciones_validas = [
            "agregar", "eliminar", "consultar", "editar",
            "consultar_tipo", "consultar_marca",
            "consultar_caducidad", "consultar_ingreso",
            "seleccionar"
        ]

        if "accion" not in accion_json or accion_json["accion"] not in acciones_validas:
            accion_json["accion"] = "error"

        if accion_json["accion"].startswith("consultar") and not accion_json.get("producto"):
            accion_json["producto"] = "Por definir"

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
