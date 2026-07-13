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

    # Detectar fechas inválidas
    fecha_regex = r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b"
    coincidencias = re.findall(fecha_regex, mensaje)
    for d, m, y in coincidencias:
        try:
            datetime(int(y), int(m), int(d))
        except:
            mensaje = mensaje.replace(f"{d}-{m}-{y}", "Por definir")

    # Inferencias de intención
    if any(x in texto for x in ["ponle", "agrega", "añade"]) and "más" in texto:
        contexto += "\n[INTENCION_INFERIDA]: edit_quantity"

    if any(x in texto for x in ["cámbial", "cambia", "actualiza", "modifica", "edita"]):
        contexto += "\n[INTENCION_INFERIDA]: edit"

    if texto in ["sí", "ok", "dale", "ese", "esa", "el primero", "el segundo"]:
        contexto += "\n[INTENCION_INFERIDA]: select"

    if texto.startswith(("agrega", "añade", "añadir", "pon ", "ponle", "registra", "ingresa")):
        contexto += "\n[FORZAR_ACCION]: add"

    if "cambia el nombre" in texto or "renombra" in texto:
        contexto += "\n[CAMBIO_NOMBRE_PRODUCTO]"

    if "cambia el rubro" in texto or "cambia la categoría" in texto or "ponlo en la categoría" in texto:
        contexto += "\n[CAMBIO_CATEGORIA]"

    # Detectar lote
    match_lote = re.search(r"lote\s*(#|\s*número\s*)?(\d+)", texto)
    lote_id_detectado = int(match_lote.group(2)) if match_lote else None

    # Prompt para Groq
    prompt = f"""
Eres Bell, un asistente experto en inventario.
Tu única salida debe ser SIEMPRE un JSON válido.
Nunca escribas texto fuera del JSON.
Nunca expliques tu razonamiento.
Nunca agregues comentarios.
Nunca conviertas unidades.
Nunca escales cantidades.
Nunca interpretes equivalencias.
Nunca transformes 1 kg → 1000 g, ni 1 L → 1000 ml, ni 500 ml → 0.5 L.
Debes usar EXACTAMENTE el contenido que el usuario menciona.

Contrato JSON obligatorio:
{{
  "action": "add" | "edit" | "delete" | "query" | "select",
  "target": {{
    "product_name": null,
    "brand": null,
    "category": null,
    "type_variety": null,
    "content_value": null,
    "content_unit": null,
    "sku_code": null
  }},
  "batch": {{
    "quantity": 0,
    "arrival_date": "{hoy}",
    "expiration_date": "Por definir",
    "batch_id": null
  }},
  "changes": {{
    "field": null,
    "value": null,
    "extra": {{}}
  }},
  "option": null
}}

INTERPRETA ESTE MENSAJE:
{mensaje}

CONTEXTO:
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

        contrato = json.loads(contenido[inicio:fin+1])

        contrato.setdefault("action", "query")
        contrato.setdefault("target", {})
        contrato.setdefault("batch", {
            "quantity": 0,
            "arrival_date": hoy,
            "expiration_date": "Por definir"
        })
        contrato.setdefault("changes", {})

        # Lote detectado
        if lote_id_detectado:
            contrato["batch"]["batch_id"] = lote_id_detectado
            if contrato["action"] == "edit":
                contrato["changes"]["field"] = "batch_quantity"

        # Normalización de fecha
        fecha = str(contrato["batch"].get("arrival_date", "")).strip()
        if "-" in fecha and len(fecha.split("-")[0]) == 4:
            contrato["batch"]["arrival_date"] = fecha
        else:
            try:
                d, m, y = fecha.split("-")
                contrato["batch"]["arrival_date"] = f"{y}-{m}-{d}"
            except:
                contrato["batch"]["arrival_date"] = hoy

        # Detectar contenido
        texto_original = mensaje.lower()
        menciona_contenido = any(
            unidad in texto_original
            for unidad in ["ml", "mililitro", "l ", "litro", "kg", "kilogramo", "g", "gramo"]
        )

        if not menciona_contenido:
            contrato["target"]["content_value"] = None
            contrato["target"]["content_unit"] = None

        # Separar contenido tipo "1kg"
        if contrato["target"].get("content_value") and contrato["target"].get("content_unit") is None:
            raw = contrato["target"]["content_value"]
            match = re.match(r"(\d+(?:\.\d+)?)([a-zA-Z]+)", raw)
            if match:
                contrato["target"]["content_value"] = match.group(1)
                contrato["target"]["content_unit"] = match.group(2)

        # 🔥 Fallback de product_name
        if not contrato["target"].get("product_name"):
            posibles = re.findall(r"[a-zA-Záéíóúñ]+", texto)
            blacklist = {
                "del", "de", "la", "el", "marca", "rubro", "variedad", "contenido",
                "kg", "g", "ml", "l", "unidades", "unidad", "ponle", "agrega",
                "añade", "ingresa", "registra", "cambia", "modifica", "actualiza",
                "quita", "elimina", "fecha", "vencimiento", "por", "definir"
            }
            for palabra in posibles:
                if palabra not in blacklist:
                    contrato["target"]["product_name"] = palabra
                    break

        # 🔥 LIMPIEZA DE NOMBRE DE PRODUCTO
        pn = contrato["target"].get("product_name")
        if pn:
            pn = pn.lower()
            pn = pn.replace("marca", "")
            pn = pn.replace("del rubro", "")
            pn = pn.replace("rubro", "")
            pn = pn.replace("contenido", "")
            pn = pn.replace("variedad", "")
            pn = pn.replace("tipo", "")

            palabras = [p for p in re.findall(r"[a-záéíóúñ]+", pn) if p not in ["la", "el", "de", "del"]]
            if palabras:
                contrato["target"]["product_name"] = palabras[0].capitalize()

        # 🔥 DETECTAR CANTIDAD PARA DELETE
        if contrato["action"] == "delete":
            match_qty = re.search(r"(\d+)", mensaje)
            if match_qty:
                contrato["batch"]["quantity"] = int(match_qty.group(1))

        return contrato

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {
            "action": "query",
            "target": {"product_name": ""},
            "batch": {
                "quantity": 0,
                "arrival_date": hoy,
                "expiration_date": "Por definir"
            },
            "changes": {},
            "option": None
        }
