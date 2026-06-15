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

    def normalizar_cantidad(valor):
        try:
            return int(valor)
        except:
            return 0

    def normalizar_fecha(valor):
        """
        Acepta:
        - "Por definir"
        - DD-MM-YYYY  → convierte a YYYY-MM-DD
        - YYYY-MM-DD → lo deja igual
        """
        if valor in ["", None, "-", "por definir", "Por definir"]:
            return "Por definir"

        try:
            if "-" in valor and len(valor.split("-")[0]) == 2:
                d, m, y = valor.split("-")
                return f"{y}-{m}-{d}"
        except:
            pass

        try:
            datetime.strptime(valor, "%Y-%m-%d")
            return valor
        except:
            return "Por definir"

    if tipo == "agregar":
        cantidad = normalizar_cantidad(accion.get("cantidad", 0))
        tipo_p = accion.get("tipo", "Por definir")
        marca = accion.get("marca", "Por definir")

        fecha_ingreso = normalizar_fecha(accion.get("fecha_ingreso", "Por definir"))
        fecha_caducidad = normalizar_fecha(accion.get("fecha_caducidad", "Por definir"))

        if fecha_ingreso == "Por definir":
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
        cantidad = normalizar_cantidad(accion.get("cantidad", 0))

        cursor.execute("SELECT * FROM productos WHERE LOWER(nombre) = LOWER(%s)", (producto,))
        productos = cursor.fetchall()

        if not productos:
            conn.close()
            return f"No existe el producto '{producto}'."

        producto_id = productos[0]["id"]

        cursor.execute("SELECT cantidad FROM productos WHERE id = %s", (producto_id,))
        cantidad_actual = cursor.fetchone()["cantidad"]

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
            conn.close()
            return "No hay selección pendiente para ese producto."

        lista = opciones_pendientes[producto]

        def fecha_key(f):
            return f if f != "Por definir" else "9999-99-99"

        if seleccion.isdigit():
            n = int(seleccion)
            if 1 <= n <= len(lista):
                elegido = lista[n - 1]
            else:
                conn.close()
                return "Número inválido. Intenta nuevamente."

        elif "marca" in seleccion:
            marca = seleccion.replace("marca", "").strip()
            coincidencias = [p for p in lista if p["marca"].lower() == marca.lower()]
            if len(coincidencias) == 1:
                elegido = coincidencias[0]
            else:
                conn.close()
                return "No encontré un producto con esa marca."

        elif "tipo" in seleccion:
            tipo_p = seleccion.replace("tipo", "").strip()
            coincidencias = [p for p in lista if p["tipo"].lower() == tipo_p.lower()]
            if len(coincidencias) == 1:
                elegido = coincidencias[0]
            else:
                conn.close()
                return "No encontré un producto con ese tipo."

        elif "nuevo" in seleccion:
            elegido = sorted(lista, key=lambda p: fecha_key(p["fecha_ingreso"]), reverse=True)[0]

        elif "viejo" in seleccion:
            elegido = sorted(lista, key=lambda p: fecha_key(p["fecha_ingreso"]))[0]

        elif "vence primero" in seleccion or "primero" in seleccion:
            validas = [p for p in lista if p["fecha_caducidad"] != "Por definir"]
            elegido = sorted(validas, key=lambda p: fecha_key(p["fecha_caducidad"]))[0]

        elif "vence después" in seleccion or "después" in seleccion:
            validas = [p for p in lista if p["fecha_caducidad"] != "Por definir"]
            elegido = sorted(validas, key=lambda p: fecha_key(p["fecha_caducidad"]), reverse=True)[0]

        else:
            conn.close()
            return "No entendí tu selección. Intenta con: '1', 'marca Polar', 'el más nuevo', etc."

        accion_original = accion.get("accion_original")
        accion_original["producto_id"] = elegido["id"]

        del opciones_pendientes[producto]

        conn.close()
        return ejecutar_accion(accion_original)


    cursor.execute("SELECT * FROM productos WHERE LOWER(nombre) = LOWER(%s)", (producto,))
    productos = cursor.fetchall()

    if tipo == "consultar":
        if len(productos) == 0:
            conn.close()
            return f"No tengo registros de '{producto}'."

        if len(productos) == 1:
            p = productos[0]
            conn.close()
            return (
                f"Producto: {p['nombre']}\n"
                f"- Cantidad: {p['cantidad']}\n"
                f"- Marca: {p['marca']}\n"
                f"- Tipo: {p['tipo']}\n"
                f"- Ingreso: {p['fecha_ingreso']}\n"
                f"- Caducidad: {p['fecha_caducidad']}"
            )

        opciones_pendientes[producto] = productos
        total = sum(p["cantidad"] for p in productos)

        respuesta = f"Lotes de {producto}:\n\n"

        for i, p in enumerate(productos, start=1):
            respuesta += (
                f"{i})\n"
                f"- Marca: {p['marca']}\n"
                f"- Tipo: {p['tipo']}\n"
                f"- Ingreso: {p['fecha_ingreso']}\n"
                f"- Caducidad: {p['fecha_caducidad']}\n"
                f"- Cantidad: {p['cantidad']}\n\n"
            )

        respuesta += f"Total disponible: {total} unidades."
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

        if not productos:
            return f"No encontré {producto} de marca {marca}."

        p = productos[0]
        return (
            f"{p['nombre']} (Marca: {p['marca']})\n"
            f"- Cantidad: {p['cantidad']}\n"
            f"- Tipo: {p['tipo']}\n"
            f"- Ingreso: {p['fecha_ingreso']}\n"
            f"- Caducidad: {p['fecha_caducidad']}"
        )

    if tipo == "consultar_tipo":
        tipo_p = accion.get("tipo", "")
        cursor.execute(
            "SELECT * FROM productos WHERE LOWER(nombre)=LOWER(%s) AND LOWER(tipo)=LOWER(%s)",
            (producto, tipo_p)
        )
        productos = cursor.fetchall()
        conn.close()

        if not productos:
            return f"No encontré {producto} de tipo {tipo_p}."

        total = sum(p["cantidad"] for p in productos)

        respuesta = f"Lotes de {producto} tipo {tipo_p}:\n\n"

        for i, p in enumerate(productos, start=1):
            respuesta += (
                f"{i})\n"
                f"- Marca: {p['marca']}\n"
                f"- Cantidad: {p['cantidad']}\n"
                f"- Ingreso: {p['fecha_ingreso']}\n"
                f"- Caducidad: {p['fecha_caducidad']}\n\n"
            )

        respuesta += f"Total disponible: {total} unidades."
        return respuesta


    if tipo == "consultar_caducidad":
        dias = int(accion.get("dias", 0))
        limite = datetime.today() + timedelta(days=dias)

        cursor.execute("SELECT * FROM productos WHERE fecha_caducidad != 'Por definir'")
        productos = cursor.fetchall()
        conn.close()

        proximos = []
        for p in productos:
            try:
                fecha = datetime.strptime(p["fecha_caducidad"], "%Y-%m-%d")
                if fecha <= limite:
                    proximos.append(p)
            except:
                continue

        if not proximos:
            return f"Ningún producto vence en {dias} días."

        respuesta = f"Productos que vencen en {dias} días:\n\n"

        for p in proximos:
            respuesta += (
                f"- {p['nombre']} (Marca: {p['marca']})\n"
                f"  Caduca: {p['fecha_caducidad']}\n"
                f"  Cantidad: {p['cantidad']}\n\n"
            )

        return respuesta

    if tipo == "consultar_ingreso":
        fecha = normalizar_fecha(accion.get("fecha_ingreso", ""))
        cursor.execute("SELECT * FROM productos WHERE fecha_ingreso = %s", (fecha,))
        productos = cursor.fetchall()
        conn.close()

        if not productos:
            return f"No se ingresaron productos en {fecha}."

        respuesta = f"Productos ingresados en {fecha}:\n\n"

        for p in productos:
            respuesta += (
                f"- {p['nombre']}\n"
                f"  Cantidad: {p['cantidad']}\n"
                f"  Marca: {p['marca']}\n"
                f"  Tipo: {p['tipo']}\n"
                f"  Caducidad: {p['fecha_caducidad']}\n\n"
            )

        return respuesta


    campos_validos = ["nombre", "cantidad", "tipo", "marca", "fecha_ingreso", "fecha_caducidad"]

    if tipo == "editar":
        campo = accion.get("campo")
        valor = accion.get("valor", "Por definir")

        if campo is None:
            conn.close()
            return "No especificaste qué campo deseas editar."

        if campo not in campos_validos:
            conn.close()
            return f"El campo '{campo}' no es válido. Campos válidos: {', '.join(campos_validos)}"

        if not productos:
            conn.close()
            return f"No existe el producto '{producto}'."

        if len(productos) > 1:
            conn.close()
            return "Hay varios lotes de este producto. Especifica marca o tipo."

        producto_id = productos[0]["id"]

        if campo == "fecha_ingreso" or campo == "fecha_caducidad":
            valor = normalizar_fecha(valor)
            if valor == "Por definir":
                valor = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(f"UPDATE productos SET {campo} = %s WHERE id = %s", (valor, producto_id))
        conn.commit()
        conn.close()
        return f"El campo '{campo}' de '{producto}' fue actualizado a '{valor}'."

    conn.close()
    return "No entendí tu solicitud."
