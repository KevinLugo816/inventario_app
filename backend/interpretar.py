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

    match_lote = re.search(r"lote\s*(#|\s*número\s*)?(\d+)", texto)
    lote_id_detectado = int(match_lote.group(2)) if match_lote else None

    prompt = f"""
Eres Bell, un asistente experto en inventario profesional.
Tu única salida debe ser SIEMPRE un JSON válido.
Nunca escribas texto fuera del JSON.

Arquitectura:
- Product
- ProductVariant
- InventoryBatch

Contrato JSON:

{{
  "action": "add" | "edit" | "delete" | "query" | "select",
  "target": {{
    "product_name": "...",
    "brand": "...",
    "category": "...",
    "type_variety": "...",
    "content_value": 0,
    "content_unit": "ml",
    "sku_code": "opcional"
  }},
  "batch": {{
    "quantity": 0,
    "arrival_date": "{hoy}",
    "expiration_date": "Por definir",
    "batch_id": "opcional"
  }},
  "changes": {{
    "field": "content_value",
    "value": 900,
    "extra": {{
      "content_unit": "ml"
    }}
  }},
  "option": "opcional"
}}

REGLAS DE ACCIONES:

ADD:
- Crear variante y lote.
- Si falta algo, usar "Por definir".

EDIT:
- Cambiar cualquier campo del producto o variante.
- Campos válidos:
  - product_name
  - category
  - brand
  - type_variety
  - content_value
  - content_unit
  - arrival_date
  - expiration_date
  - batch_quantity (requiere batch_id)

DELETE:
- Eliminar cantidad de una variante.

QUERY:
- Consultar producto/variante.

SELECT:
- Selección de opciones.

REGLAS DE CONTENIDO:
- NO convertir unidades.
- NO escalar unidades.
- NO interpretar equivalencias.
- SOLO usar el contenido EXACTO que el usuario menciona.

REGLAS DE FECHAS:
- arrival_date por defecto = "{hoy}"
- Si el usuario dice "por definir", usar "Por definir".

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

        if lote_id_detectado:
            contrato["batch"]["batch_id"] = lote_id_detectado
            if contrato["action"] == "edit":
                contrato["changes"]["field"] = "batch_quantity"

        fecha = str(contrato["batch"].get("arrival_date", "")).strip()
        if fecha.lower() in ["", "por definir", "-", "none", "null"]:
            contrato["batch"]["arrival_date"] = hoy
        else:
            try:
                if "-" in fecha and len(fecha.split("-")[0]) == 4:
                    y, m, d = fecha.split("-")
                    contrato["batch"]["arrival_date"] = f"{d}-{m}-{y}"
            except:
                contrato["batch"]["arrival_date"] = hoy

        texto_original = mensaje.lower()

        menciona_contenido = any(
            unidad in texto_original
            for unidad in ["ml", "mililitro", "l ", "litro", "kg", "kilogramo", "g", "gramo"]
        )

        if not menciona_contenido:
            contrato["target"]["content_value"] = None
            contrato["target"]["content_unit"] = None

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
