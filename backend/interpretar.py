import json
import os
import re
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str, contexto: str = ""):
    hoy = datetime.now().strftime("%d-%m-%Y")
    texto = mensaje.lower()

    fecha_regex = r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b"
    coincidencias = re.findall(fecha_regex, mensaje)
    for d, m, y in coincidencias:
        try:
            datetime(int(y), int(m), int(d))
        except:
            mensaje = mensaje.replace(f"{d}-{m}-{y}", "Por definir")

    if any(x in texto for x in ["ponle", "agrega", "añade"]) and "más" in texto:
        contexto += "\n[INTENCION_INFERIDA]: editar_cantidad"

    if "cámbial" in texto or "actualiza" in texto:
        contexto += "\n[INTENCION_INFERIDA]: editar"

    if texto.strip() in ["sí", "ok", "dale", "ese", "esa", "el primero", "el segundo"]:
        contexto += "\n[INTENCION_INFERIDA]: seleccionar"

    def singularizar(p):
        p = p.lower().strip()
        if p.endswith("es"):
            return p[:-2]
        if p.endswith("s"):
            return p[:-1]
        return p

    prompt = f"""
Eres Bell, un asistente experto en inventario profesional.  
Tu única salida debe ser SIEMPRE un JSON válido.  
Nunca escribas texto fuera del JSON.

ANTES DE RESPONDER:
- Analiza la intención del usuario.
- Analiza el contexto previo.
- Analiza si el usuario está continuando una selección.
- Analiza si el usuario está corrigiendo un mensaje anterior.
- Analiza si el usuario está dando una instrucción implícita.
- No muestres tu razonamiento interno.

OBJETIVO:
Interpretar el mensaje del usuario y devolver un JSON con la acción correcta y los campos necesarios.

REGLAS GENERALES:
- SOLO JSON puro.
- Si falta un campo, usa "Por definir".
- arrival_date por defecto = fecha actual en DD-MM-YYYY.
- Convierte plurales a singular (aceites → aceite).
- Si el usuario dice "por definir", respétalo.
- Si el usuario menciona dos acciones, elige SOLO la más importante.
- Prioridad: agregar > editar > eliminar > consultar.
- Si el usuario consulta por marca, tipo, categoría o contenido, SIEMPRE incluye "producto".
- Si el usuario consulta cantidades, SIEMPRE incluye "producto".
- Si el usuario está eligiendo entre variantes, acción = seleccionar.
- Si el mensaje es ambiguo pero existe contexto suficiente, NO pidas aclaración: usa el contexto.
- Si detectas inconsistencias (fechas inválidas, cantidades negativas, valores faltantes), corrige y marca "opcion": "correccion".
- Si el usuario responde con algo corto como "marca X", "el más nuevo", "el que vence primero", "2", "ese", "sí", "ok", "dale", entonces acción = seleccionar.

REGLAS DE INTENCIÓN IMPLÍCITA:
- "agrega X más", "ponle X más", "añade X más" → acción = editar, campo = cantidad.
- "cámbiale", "actualiza", "modifica" → acción = editar.
- "quita", "remueve", "descarta" → acción = eliminar.
- "cuánto hay", "cuánta cantidad", "cuántos quedan" → acción = consultar.
- "qué marca tiene", "qué tipo es", "qué contenido tiene" → acción = consultar.

ACCIONES DISPONIBLES:
- agregar
- eliminar
- consultar
- editar
- seleccionar

CAMPOS DISPONIBLES:
- producto
- brand
- category
- type_variety
- content_value
- content_unit
- cantidad
- arrival_date
- expiration_date
- campo
- valor
- opcion

FORMATO DE PRODUCTO PROFESIONAL:
- producto: nombre del producto en singular
- brand: marca
- category: rubro/categoría
- type_variety: variedad o tipo
- content_value: número (1, 500)
- content_unit: unidad (L, ml, g, kg)
- cantidad: unidades del lote
- arrival_date: DD-MM-YYYY
- expiration_date: DD-MM-YYYY o "Por definir"

USO DEL CONTEXTO:
- Si el usuario no menciona producto explícito pero existe un producto en CONTEXTO PREVIO, úsalo.
- Si el usuario está respondiendo a una selección pendiente, acción = seleccionar.

INTERPRETA ESTE MENSAJE:
{mensaje}

CONTEXTO PREVIO:
{contexto}

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

        acciones_validas = ["agregar", "eliminar", "consultar", "editar", "seleccionar"]
        if accion_json.get("accion") not in acciones_validas:
            accion_json["accion"] = "error"

        fecha = accion_json.get("arrival_date", "").strip()

        if fecha.lower() in ["", "por definir", "-", "none", "null"]:
            accion_json["arrival_date"] = hoy
        else:
            try:
                if "-" in fecha and len(fecha.split("-")[0]) == 4:
                    y, m, d = fecha.split("-")
                    accion_json["arrival_date"] = f"{d}-{m}-{y}"
            except:
                accion_json["arrival_date"] = hoy

        if accion_json.get("accion") == "editar":
            campo = accion_json.get("campo")

            if not campo:
                if "marca" in texto:
                    campo = "brand"
                elif "categoria" in texto or "rubro" in texto:
                    campo = "category"
                elif "tipo" in texto or "variedad" in texto:
                    campo = "type_variety"
                elif "contenido" in texto:
                    if any(u in texto for u in ["ml", "l", "kg", "g"]):
                        campo = "content_unit"
                    else:
                        campo = "content_value"
                elif "ingreso" in texto:
                    campo = "arrival_date"
                elif "caduc" in texto or "vence" in texto:
                    campo = "expiration_date"

                accion_json["campo"] = campo if campo else "Por definir"

            if accion_json.get("valor") in [None, "", "Por definir"]:
                if accion_json["campo"] in accion_json:
                    accion_json["valor"] = accion_json[accion_json["campo"]]

        if accion_json.get("accion") == "eliminar":
            if accion_json.get("cantidad", 0) < 0:
                accion_json["cantidad"] = abs(accion_json["cantidad"])

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
