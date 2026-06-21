import json
import os
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def interpretar_mensaje(mensaje: str, contexto: str = ""):
    hoy = datetime.now().strftime("%d-%m-%Y")

    def singularizar(p):
        p = p.lower().strip()
        if p.endswith("es"):
            return p[:-2]
        if p.endswith("s"):
            return p[:-1]
        return p

    prompt = f"""
Eres Bell, un asistente experto en inventario profesional.
Responde SOLO con JSON válido. NO escribas nada fuera del JSON.

REGLAS GENERALES:
- SOLO JSON puro.
- Si falta un campo, usa "Por definir".
- Si falta arrival_date, usa la fecha actual en DD-MM-YYYY.
- Si el usuario dice "por definir", respétalo.
- Convierte plurales a singular (aceites → aceite).
- Si el usuario menciona dos acciones, elige SOLO la más importante.
- Prioridad: agregar > editar > eliminar > consultar.
- Si el usuario consulta por marca, tipo, categoría o contenido, SIEMPRE incluye "producto".
- Si el usuario consulta cantidades, SIEMPRE incluye "producto".
- Si el usuario está eligiendo entre variantes, acción = seleccionar.

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
            texto = mensaje.lower()
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
                elif "alerta" in texto or "mínimo" in texto:
                    campo = "stock_alert"
                elif "ingreso" in texto:
                    campo = "arrival_date"
                elif "caduc" in texto or "vence" in texto:
                    campo = "expiration_date"

                accion_json["campo"] = campo if campo else "Por definir"

            # Si falta valor, usar el que vino en el JSON
            if accion_json.get("valor") in [None, "", "Por definir"]:
                if accion_json["campo"] in accion_json:
                    accion_json["valor"] = accion_json[accion_json["campo"]]

        return accion_json

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {"accion": "error", "producto": "", "cantidad": 0}
