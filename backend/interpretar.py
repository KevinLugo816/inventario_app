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
    texto = mensaje.lower().strip()

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

    if texto in ["sí", "ok", "dale", "ese", "esa", "el primero", "el segundo"]:
        contexto += "\n[INTENCION_INFERIDA]: seleccionar"

    if texto.startswith(("agrega", "añade", "añadir", "pon ", "ponle", "registra", "ingresa")):
        contexto += "\n[FORZAR_ACCION]: agregar"

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
- Convierte plurales a singular.
- Si el usuario dice "por definir", respétalo.
- Prioridad: agregar > editar > eliminar > consultar.
- Si el usuario consulta por marca, tipo, categoría o contenido, incluye "producto".
- Si el usuario consulta cantidades, incluye "producto".
- Si el usuario está eligiendo entre variantes, acción = seleccionar.
- Si el mensaje es ambiguo pero existe contexto suficiente, usa el contexto.
- Si detectas inconsistencias, corrige y marca "opcion": "correccion".

REGLA CRÍTICA PARA AGREGAR:
Si el mensaje empieza con "agrega", "añade", "añadir", "pon", "ponle", "registra", "ingresa",
la acción SIEMPRE debe ser "agregar".

Si CONTEXTO PREVIO contiene "[FORZAR_ACCION]: agregar", entonces la acción debe ser "agregar".

Para la acción "agregar", SIEMPRE debes devolver al menos:

{{
  "accion": "agregar",
  "producto": "...",
  "cantidad": 0,
  "brand": "Por definir",
  "category": "Por definir",
  "type_variety": "Por definir",
  "content_value": "Por definir",
  "content_unit": "Por definir",
  "arrival_date": "{hoy}",
  "expiration_date": "Por definir"
}}

Si el usuario no menciona un campo, rellénalo con "Por definir" o 0.

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
                    match = re.search(r"(\d+)\s*(ml|l|kg|g)", texto)
                    if match:
                        accion_json["campo"] = "content_value"
                        accion_json["valor"] = match.group(1)
                        accion_json["content_unit"] = match.group(2)
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

        if accion_json.get("accion") == "agregar":
            obligatorios = [
                "producto", "cantidad", "brand", "category",
                "type_variety", "content_value", "content_unit",
                "arrival_date", "expiration_date"
            ]
            for c in obligatorios:
                if c not in accion_json or accion_json[c] in ["", None]:
                    accion_json[c] = "Por definir" if c != "cantidad" else 0

        if accion_json.get("accion") == "seleccionar":
            if not accion_json.get("producto"):
                accion_json["producto"] = "por_definir"

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
