from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import db, Category, Brand, Product, ProductVariant, InventoryBatch
from interpretar import interpretar_mensaje
from ejecutar import ejecutar_accion
import os
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/api/inventario", methods=["GET"])
def inventario():
    try:
        productos = Product.query.all()
        resultado = []

        for p in productos:
            producto_json = {
                "id": p.id,
                "name": p.name,
                "category": p.category.name if p.category else None,
                "variants": []
            }

            for v in p.variants:
                lotes = InventoryBatch.query.filter_by(variant_id=v.id).all()
                total = sum(l.quantity for l in lotes)

                variante_json = {
                    "variant_id": v.id,
                    "brand": v.brand.name if v.brand else None,
                    "type_variety": v.type_variety,
                    "content_value": v.content_value,
                    "content_unit": v.content_unit,
                    "sku_code": v.sku_code,
                    "total_quantity": total,
                    "batches": [
                        {
                            "id": l.id,
                            "quantity": l.quantity,
                            "arrival_date": l.arrival_date.strftime("%Y-%m-%d"),
                            "expiration_date": (
                                l.expiration_date.strftime("%Y-%m-%d")
                                if l.expiration_date else None
                            )
                        }
                        for l in lotes
                    ]
                }

                producto_json["variants"].append(variante_json)

            resultado.append(producto_json)

        return jsonify({"productos": resultado})

    except Exception as e:
        print("Error en /api/inventario:", e)
        return jsonify({"error": "Error obteniendo inventario"}), 500


@app.route("/asistente_ia", methods=["POST"])
def asistente_ia():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")
        contexto = data.get("contexto", "")

        if not mensaje:
            return jsonify({"respuesta": "No recibí ningún mensaje."})

        try:
            accion = interpretar_mensaje(mensaje, contexto=contexto)
        except Exception as e:
            print("Error interpretando mensaje:", e)
            return jsonify({"respuesta": "No pude interpretar tu mensaje."})

        if not isinstance(accion, dict):
            return jsonify({"respuesta": "La IA devolvió un formato inesperado."})

        if accion.get("accion") == "error":
            return jsonify({"respuesta": "No entendí tu solicitud."})

        try:
            resultado = ejecutar_accion(accion)
        except Exception as e:
            print("Error ejecutando acción:", e)
            return jsonify({"respuesta": "Ocurrió un error ejecutando la acción."})

        time.sleep(0.2)

        return jsonify({"respuesta": resultado})

    except Exception as e:
        print("Error en /asistente_ia:", e)
        return jsonify({"respuesta": "Ocurrió un error procesando tu solicitud."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
