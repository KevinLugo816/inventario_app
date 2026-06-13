from datetime import datetime, timedelta
from database import get_connection
import psycopg2.extras

opciones_pendientes = {}

def ejecutar_accion(accion):
    global opciones_pendientes

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    tipo = accion.get("accion")
    producto = accion.get("producto", "").strip().lower()

    print(f"Acción: {tipo} | Producto: {producto} | Datos: {accion}")

    if tipo == "agregar":
        cantidad = accion.get("cantidad", 0)
        tipo_p = accion.get("tipo", "Por definir")
        marca = accion.get("marca", "Por definir")
        fecha_ingreso = accion.get("fecha_ingreso", "Por definir")
        fecha_caducidad = accion.get("fecha_caducidad", "Por definir")

        # Normalizar fecha_ingreso
        if fecha_ingreso in ["", None, "Por definir", "-", "por definir"]:
            fecha_ingreso = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                fecha_dt = datetime.strptime(fecha_ingreso, "%Y-%m-%d")
                if fecha_dt.year != datetime.now().year:
                    fecha_ingreso = datetime.now().strftime("%Y-%m-%d")
            except:
                fecha_ingreso = datetime.now().strftime("%Y-%m-%d")

        producto_id = accion.get("producto_id")

        if producto_id:
            cursor.execute("""
                UPDATE productos SET 
                    cantidad = cantidad + %s,
                    tipo = CASE WHEN %s != 'Por definir' THEN %s ELSE tipo END,
                    marca = CASE WHEN %s != 'Por definir' THEN %s ELSE marca END,
                    fecha_ingreso = CASE WHEN %s != 'Por definir' THEN %s ELSE fecha_ingreso END,
                    fecha_caducidad = CASE WHEN %s != 'Por definir' THEN %s ELSE fecha_caducidad END
                WHERE id = %s
            """, (
                cantidad, tipo_p, tipo_p,
                marca, marca,
                fecha_ingreso, fecha_ingreso,
                fecha_caducidad, fecha_caducidad,
                producto_id
            ))

        else:
            cursor.execute("""
                INSERT INTO productos (nombre, cantidad, tipo, marca, fecha_ingreso, fecha_caducidad)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (producto, cantidad, tipo_p, marca, fecha_ingreso, fecha_caducidad))

        conn.commit()
        conn.close()
        return f"Se agregaron {cantidad} unidades de '{producto}' (Marca: {marca}, Tipo: {tipo_p})."

    elif tipo == "eliminar":
        cantidad = accion.get("cantidad", 0)

        cursor.execute("SELECT * FROM productos WHERE LOWER(nombre) = LOWER(%s)", (producto,))
        productos = cursor.fetchall()

        if not productos:
            conn.close()
            return f"No existe el producto '{producto}'."

        producto_id = productos[0]["id"]

        cursor.execute("SELECT cantidad FROM productos WHERE id = %s", (producto_id,))
        dato = cursor.fetchone()
        cantidad_actual = dato["cantidad"]

        if cantidad == 0:
            cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
            conn.commit()
            conn.close()
            return f"Producto '{producto}' eliminado completamente."

        if cantidad > cantidad_actual:
            conn.close()
            return f"No puedes eliminar {cantidad}. Solo hay {cantidad_actual} unidades disponibles."

        nueva = cantidad_actual - cantidad

        if nueva == 0:
            cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
            mensaje = f"Se eliminaron todas las unidades de '{producto}'."
        else:
            cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva, producto_id))
            mensaje = f"Se eliminaron {cantidad} unidades de '{producto}'. Quedan {nueva}."

        conn.commit()
        conn.close()
        return mensaje

    if tipo == "seleccionar":
        seleccion = accion.get("opcion", "").lower()

        if producto not in opciones_pendientes:
            return "No hay selección pendiente para ese producto."

        lista = opciones_pendientes[producto]

        if seleccion.isdigit():
            n = int(seleccion)
            if 1 <= n <= len(lista):
                elegido = lista[n - 1]
            else:
                return "Número inválido. Intenta nuevamente."

        elif "marca" in seleccion:
            marca = seleccion.replace("marca", "").strip()
            coincidencias = [p for p in lista if p["marca"].lower() == marca.lower()]
            if len(coincidencias) == 1:
                elegido = coincidencias[0]
            else:
                return "No encontré un producto con esa marca."

        elif "tipo" in seleccion:
            tipo_p = seleccion.replace("tipo", "").strip()
            coincidencias = [p for p in lista if p["tipo"].lower() == tipo_p.lower()]
            if len(coincidencias) == 1:
                elegido = coincidencias[0]
            else:
                return "No encontré un producto con ese tipo."

        elif "nuevo" in seleccion:
            lista_ordenada = sorted(lista, key=lambda p: p["fecha_ingreso"], reverse=True)
            elegido = lista_ordenada[0]

        elif "viejo" in seleccion:
            lista_ordenada = sorted(lista, key=lambda p: p["fecha_ingreso"])
            elegido = lista_ordenada[0]

        elif "vence primero" in seleccion or "primero" in seleccion:
            lista_validas = [p for p in lista if p["fecha_caducidad"] != "Por definir"]
            lista_ordenada = sorted(lista_validas, key=lambda p: p["fecha_caducidad"])
            elegido = lista_ordenada[0]

        elif "vence después" in seleccion or "después" in seleccion:
            lista_validas = [p for p in lista if p["fecha_caducidad"] != "Por definir"]
            lista_ordenada = sorted(lista_validas, key=lambda p: p["fecha_caducidad"], reverse=True)
            elegido = lista_ordenada[0]

        else:
            return "No entendí tu selección. Intenta con: '1', 'marca Polar', 'el más nuevo', etc."

        accion_original = accion.get("accion_original")
        accion_original["producto_id"] = elegido["id"]

        del opciones_pendientes[producto]

        return ejecutar_accion(accion_original)

    cursor.execute("SELECT * FROM productos WHERE LOWER(nombre) = LOWER(%s)", (producto,))
    productos = cursor.fetchall()

    if tipo == "consultar":
        if len(productos) == 0:
            conn.close()
            return f"No tengo registros de '{producto}'."
        elif len(productos) == 1:
            p = productos[0]
            conn.close()
            return (f"Producto: {p['nombre']} | Cantidad: {p['cantidad']} | "
                    f"Marca: {p['marca']} | Tipo: {p['tipo']} | "
                    f"Ingreso: {p['fecha_ingreso']} | Caducidad: {p['fecha_caducidad']}")
        else:
            total = sum(p["cantidad"] for p in productos)
            respuesta = f"Tengo varios lotes de '{producto}':\n\n"
            for i, p in enumerate(productos, start=1):
                respuesta += (f"{i}) Marca: {p['marca']} | Tipo: {p['tipo']} | "
                              f"Ingreso: {p['fecha_ingreso']} | Caducidad: {p['fecha_caducidad']} | "
                              f"Cantidad: {p['cantidad']}\n")
            respuesta += f"\nTotal disponible: {total} unidades."
            conn.close()
            return respuesta

    if tipo == "consultar_marca":
        marca = accion.get("marca", "")
        cursor.execute(
            "SELECT * FROM productos WHERE LOWER(nombre)=LOWER(%s) AND LOWER(marca)=LOWER(%s)",
            (producto, marca)
        )
        productos = cursor.fetchall()
        conn.close()
        if productos:
            p = productos[0]
            return f"{p['nombre']} marca {p['marca']} → {p['cantidad']} unidades, vence {p['fecha_caducidad']}."
        return f"No encontré {producto} de marca {marca}."

    if tipo == "consultar_tipo":
        tipo_p = accion.get("tipo", "")
        cursor.execute(
            "SELECT * FROM productos WHERE LOWER(nombre)=LOWER(%s) AND LOWER(tipo)=LOWER(%s)",
            (producto, tipo_p)
        )
        productos = cursor.fetchall()
        conn.close()
        if productos:
            total = sum(p["cantidad"] for p in productos)
            return f"{producto} tipo {tipo_p} → {total} unidades."
        return f"No encontré {producto} de tipo {tipo_p}."

    if tipo == "consultar_caducidad":
        dias = int(accion.get("dias", 0))
        limite = datetime.today() + timedelta(days=dias)

        cursor.execute("SELECT * FROM productos WHERE fecha_caducidad != 'Por definir'")
        productos = cursor.fetchall()

        proximos = []
        for p in productos:
            try:
                fecha = datetime.strptime(p["fecha_caducidad"], "%Y-%m-%d")
                if fecha <= limite:
                    proximos.append(p)
            except:
                continue

        conn.close()

        if proximos:
            respuesta = f"Productos que vencen en {dias} días:\n"
            for p in proximos:
                respuesta += f"- {p['nombre']} ({p['marca']}) vence {p['fecha_caducidad']}\n"
            return respuesta

        return f"Ningún producto vence en {dias} días."

    if tipo == "consultar_ingreso":
        fecha = accion.get("fecha_ingreso", "")
        cursor.execute("SELECT * FROM productos WHERE fecha_ingreso = %s", (fecha,))
        productos = cursor.fetchall()
        conn.close()

        if productos:
            respuesta = f"Productos ingresados en {fecha}:\n"
            for p in productos:
                respuesta += f"- {p['nombre']} ({p['cantidad']} unidades)\n"
            return respuesta

        return f"No se ingresaron productos en {fecha}."

    campos_validos = ["nombre", "cantidad", "tipo", "marca", "fecha_ingreso", "fecha_caducidad"]

    if tipo == "editar":
        campo = accion.get("campo")
        valor = accion.get("valor", "Por definir")

        if campo not in campos_validos:
            conn.close()
            return f"El campo '{campo}' no es válido."

        if not productos:
            conn.close()
            return f"No existe el producto '{producto}'."

        producto_id = productos[0]["id"]

        cursor.execute(f"UPDATE productos SET {campo} = %s WHERE id = %s", (valor, producto_id))
        conn.commit()
        conn.close()
        return f"El campo '{campo}' de '{producto}' fue actualizado a '{valor}'."

    conn.close()
    return "No entendí tu solicitud."
