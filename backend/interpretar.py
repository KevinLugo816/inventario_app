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

    if any(x in texto for x in ["cámbial", "cambia", "actualiza", "modifica"]):
        contexto += "\n[INTENCION_INFERIDA]: edit"

    if texto in ["sí", "ok", "dale", "ese", "esa", "el primero", "el segundo"]:
        contexto += "\n[INTENCION_INFERIDA]: select"

    if texto.startswith(("agrega", "añade", "añadir", "pon ", "ponle", "registra", "ingresa")):
        contexto += "\n[FORZAR_ACCION]: add"

    prompt = f"""
Eres Bell, un asistente experto en inventario profesional.
Tu única salida debe ser SIEMPRE un JSON válido.
Nunca escribas texto fuera del JSON.

Ahora trabajas con una arquitectura profesional de inventario con:
- Product (producto base)
- ProductVariant (variante / SKU)
- InventoryBatch (lotes)

Tu tarea es interpretar el mensaje del usuario y devolver un CONTRATO JSON con esta estructura:

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
    "expiration_date": "Por definir"
  }},
  "changes": {{
    "field": "content_value",
    "value": 900,
    "extra": {{
      "content_unit": "ml"
    }}
  }},
  "option": "opcional para selección"
}}

REGLAS:

- SOLO JSON puro.
- "action" debe ser una de: "add", "edit", "delete", "query", "select".
- "target.product_name" SIEMPRE debe estar si el usuario menciona un producto.
- Si el usuario menciona marca, variedad, contenido, unidad, inclúyelos en "target".
- Para "add":
  - Usa "action": "add".
  - Llena "target" con la descripción del producto/variante.
  - Llena "batch" con cantidad y fechas.
  - Si falta algo, usa "Por definir" o 0.
- Para "edit":
  - Usa "action": "edit".
  - "target" identifica el producto/variante.
  - "changes" indica qué campo se modifica.
  - Ejemplo: cambiar contenido del aceite a 900 ml:
    "changes": {{
      "field": "content_value",
      "value": 900,
      "extra": {{
        "content_unit": "ml"
      }}
    }}
- Para "delete":
  - Usa "action": "delete".
  - "target" identifica el producto/variante.
  - "batch.quantity" indica cuánto eliminar.
- Para "query":
  - Usa "action": "query".
  - "target" describe qué producto/variante consultar.
- Para "select":
  - Usa "action": "select".
  - "option" indica la selección (número o descripción).

REGLAS DE FECHAS:
- arrival_date por defecto = fecha actual en DD-MM-YYYY: "{hoy}".
- Si el usuario dice "por definir" para fechas, usa "Por definir".

REGLAS DE CONTENIDO:
- La IA NO debe convertir unidades.
- Si el usuario dice "1 litro", entonces:
  - content_value = 1
  - content_unit = "litro"
- Si el usuario dice "1000 ml", entonces:
  - content_value = 1000
  - content_unit = "ml"
- Si el usuario dice "1 kg", entonces:
  - content_value = 1
  - content_unit = "kg"
- Si el usuario dice "contenido", pero no valor, usa:
  - content_value = "Por definir"
  - content_unit = "Por definir"
- NO convertir litros a ml, ni ml a litros, ni kg a g, ni ninguna otra transformación.
- NO interpretar "1 litro" como "1000 ml".
- NO escalar unidades.
- NO asumir equivalencias.
- SOLO extraer exactamente lo que el usuario dijo.

IMPORTANTE:
- Si el usuario dice "litro", "litros" o "l", NO convertir a "ml".
- Si el usuario dice "kg", "kilogramo", "kilogramos", NO convertir a "g".
- Si el usuario dice "ml", "mililitro", "mililitros", NO convertir a "litro".
- Se debe respetar la unidad EXACTA escrita por el usuario.

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
        contrato = json.loads(contenido)


        if "action" not in contrato:
            contrato["action"] = "query"

        if "target" not in contrato or not isinstance(contrato["target"], dict):
            contrato["target"] = {}

        if "batch" not in contrato or not isinstance(contrato.get("batch"), dict):
            contrato["batch"] = {
                "quantity": 0,
                "arrival_date": hoy,
                "expiration_date": "Por definir"
            }

        if "changes" not in contrato or not isinstance(contrato.get("changes"), dict):
            contrato["changes"] = {}

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

        if contrato["changes"].get("field") == "content_value":
            valor = contrato["changes"].get("value")
            extra = contrato["changes"].get("extra", {})

            if isinstance(valor, str):
                match = re.search(r"(\d+)\s*(ml|l|kg|g)|(\d+)(ml|l|kg|g)", valor.lower())
                if match:
                    numero = match.group(1) or match.group(3)
                    unidad = match.group(2) or match.group(4)
                    contrato["changes"]["value"] = float(numero)
                    extra["content_unit"] = unidad
                    contrato["changes"]["extra"] = extra

        return contrato

    except Exception as e:
        print("Error interpretando mensaje:", e)
        return {
            "action": "query",
            "target": {
                "product_name": "",
            },
            "batch": {
                "quantity": 0,
                "arrival_date": hoy,
                "expiration_date": "Por definir"
            },
            "changes": {},
            "option": None
        }
