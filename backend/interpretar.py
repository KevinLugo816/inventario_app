import json
from groq import Groq
import os
from datetime import datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str):
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

REGLAS GENERALES:
- SOLO JSON puro.
- Si falta un campo, usa "Por definir".
- Si falta fecha_ingreso, usa la fecha actual en DD-MM-YYYY.
- Si el usuario dice "por definir", respétalo.
- Convierte plurales a singular (aceites → aceite).
- Si el usuario menciona dos acciones, responde SOLO la más importante.
- Prioridad de interpretación: agregar > editar > eliminar > consultar > seleccionar.

REGLAS PARA AGREGAR:
- Si el usuario dice "agrega X producto", acción = agregar.
- Si el usuario dice "agrega X más" o "ponle X más", acción = editar (cantidad).

REGLAS PARA EDITAR:
- Si el usuario dice "cambia", "modifica", "actualiza", "edita", acción = editar.
- En edición, usa SIEMPRE:
  - "campo": nombre del campo a editar (cantidad, marca, tipo, nombre, fecha_ingreso, fecha_caducidad).
  - "valor": nuevo valor.
- Si el usuario dice "quise decir", acción = editar.

REGLAS PARA CONSULTAR:
- Si el usuario pregunta "cuánto queda", "cuánto hay", "qué cantidad", acción = consultar.
- Si consulta por marca, acción = consultar_marca.
- Si consulta por tipo, acción = consultar_tipo.
- Si consulta por caducidad, acción = consultar_caducidad.
- Si consulta por fecha de ingreso, acción = consultar_ingreso.
- TODAS las consultas deben incluir "producto".

REGLAS PARA SELECCIONAR (MUY IMPORTANTE):
- Si hay varios lotes del mismo producto, acción = seleccionar.
- Si el usuario responde con algo corto como:
  - "marca Mary"
  - "marca Girasol"
  - "tipo Condimento"
  - "2"
  - "el más nuevo"
  - "el más viejo"
  - "el que vence primero"
  - "el que vence después"
  entonces acción = seleccionar.
- Si el mensaje NO menciona explícitamente un producto, y parece una respuesta a una selección previa, acción = seleccionar.
- En selección:
  - "producto": null
  - "opcion": texto exacto del usuario

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

Interpreta este mensaje del usuario:
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

        if "producto" in accion_json:
            accion_json["producto"] = singularizar(accion_json["producto"])

        acciones_validas = [
            "agregar", "eliminar", "consultar", "editar",
            "consultar_tipo", "consultar_marca",
            "consultar_caducidad", "consultar_ingreso",
            "seleccionar"
        ]

        if accion_json.get("accion") not in acciones_validas:
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

        if accion_json.get("accion") == "editar":
            texto = mensaje.lower()

            campo = accion_json.get("campo")
            if not campo:
                if "marca" in texto:
                    campo = "marca"
                elif "tipo" in texto:
                    campo = "tipo"
                elif "cantidad" in texto or "cuánto" in texto or "cuantos" in texto:
                    campo = "cantidad"
                elif "nombre" in texto or "producto" in texto:
                    campo = "nombre"
                elif "fecha de ingreso" in texto or "fecha ingreso" in texto:
                    campo = "fecha_ingreso"
                elif "fecha de caducidad" in texto or "vence" in texto or "caducidad" in texto:
                    campo = "fecha_caducidad"
                accion_json["campo"] = campo if campo else "Por definir"

            if accion_json.get("valor") in [None, "", "Por definir"]:
                if accion_json.get("campo") == "marca" and accion_json.get("marca"):
                    accion_json["valor"] = accion_json["marca"]
                elif accion_json.get("campo") == "tipo" and accion_json.get("tipo"):
                    accion_json["valor"] = accion_json["tipo"]
                elif accion_json.get("campo") == "nombre" and accion_json.get("producto"):
                    accion_json["valor"] = accion_json["producto"]
                elif accion_json.get("campo") == "cantidad" and accion_json.get("cantidad") not in [None, ""]:
                    accion_json["valor"] = accion_json["cantidad"]
                elif accion_json.get("campo") in ["fecha_ingreso", "fecha_caducidad"] and accion_json.get("fecha_ingreso"):
                    accion_json["valor"] = accion_json["fecha_ingreso"]

        texto = mensaje.lower()

        patrones_respuesta = [
            "marca", "tipo", "lote", "nuevo", "viejo",
            "vence", "primero", "después", "despues"
        ]

        if accion_json.get("accion") in ["consultar", "consultar_marca", "consultar_tipo", "consultar_ingreso"]:
            if any(p in texto for p in patrones_respuesta) or texto.strip().isdigit():
                accion_json["accion"] = "seleccionar"
                accion_json["opcion"] = mensaje
                accion_json["producto"] = None

        if accion_json.get("accion") == "seleccionar":
            if accion_json.get("producto") in ["", "por definir", "Por definir", None]:
                if any(p in texto for p in patrones_respuesta) or texto.strip().isdigit():
                    accion_json["producto"] = None

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
