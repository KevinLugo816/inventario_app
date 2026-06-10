from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_connection
from interpretar import interpretar_mensaje
from ejecutar import ejecutar_accion
import os

app = Flask(__name__)
CORS(app)


@app.route("/api/inventario", methods=["GET"])
def inventario():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        productos = cursor.execute("SELECT * FROM productos").fetchall()
        conn.close()

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

        # Interpretar mensaje con IA
        accion = interpretar_mensaje(mensaje)

        # Ejecutar acción en el inventario
        resultado = ejecutar_accion(accion)

        return jsonify({"respuesta": resultado})

    except Exception as e:
        print("Error en /asistente_ia:", e)
        return jsonify({"respuesta": "Ocurrió un error procesando tu solicitud."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
