from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_connection
from interpretar import interpretar_mensaje
from ejecutar import ejecutar_accion
from database import crear_tabla
import os

app = Flask(__name__)
CORS(app)

crear_tabla()

@app.route("/api/inventario", methods=["GET"])
def inventario():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()

        conn.close()

        if not productos:
            return jsonify({"productos": []})

        return jsonify({
            "productos": [dict(p) for p in productos]
        })

    except Exception as e:
        print("Error en /api/inventario:", e)
        return jsonify({"error": "Error obteniendo inventario"}), 500


@app.route("/asistente_ia", methods=["POST"])
def asistente_ia():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")

        if not mensaje:
            return jsonify({"respuesta": "No recibí ningún mensaje."})

        try:
            accion = interpretar_mensaje(mensaje)
        except Exception as e:
            print("Error interpretando mensaje:", e)
            return jsonify({"respuesta": "No pude interpretar tu mensaje."})

        if not isinstance(accion, dict):
            return jsonify({"respuesta": "La IA devolvió un formato inesperado."})

        try:
            resultado = ejecutar_accion(accion)
        except Exception as e:
            print("Error ejecutando acción:", e)
            return jsonify({"respuesta": "Ocurrió un error ejecutando la acción."})

        return jsonify({"respuesta": resultado})

    except Exception as e:
        print("Error en /asistente_ia:", e)
        return jsonify({"respuesta": "Ocurrió un error procesando tu solicitud."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
