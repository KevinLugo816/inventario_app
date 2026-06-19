from datetime import datetime
from models import db, Category, Brand, Product, InventoryBatch

opciones_pendientes = {}


def normalizar_cantidad(valor):
    try:
        return int(valor)
    except:
        return 0


def normalizar_fecha(valor):
    if not valor or valor in ["-", "por definir", "Por definir", None]:
        return None

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
        return None


def obtener_o_crear_categoria(nombre):
    if not nombre:
        nombre = "General"

    cat = Category.query.filter_by(name=nombre).first()
    if not cat:
        cat = Category(name=nombre)
        db.session.add(cat)
        db.session.commit()
    return cat


def obtener_o_crear_marca(nombre):
    if not nombre:
        nombre = "Sin marca"

    marca = Brand.query.filter_by(name=nombre).first()
    if not marca:
        marca = Brand(name=nombre)
        db.session.add(marca)
        db.session.commit()
    return marca


def obtener_o_crear_producto(nombre, marca, categoria, tipo, contenido_valor, contenido_unidad, alerta):
    prod = Product.query.filter_by(
        name=nombre,
        brand_id=marca.id,
        category_id=categoria.id,
        type_variety=tipo,
        content_value=contenido_valor,
        content_unit=contenido_unidad
    ).first()

    if not prod:
        prod = Product(
            name=nombre,
            brand_id=marca.id,
            category_id=categoria.id,
            type_variety=tipo,
            content_value=contenido_valor,
            content_unit=contenido_unidad,
            stock_alert=alerta
        )
        db.session.add(prod)
        db.session.commit()

    return prod


def ejecutar_accion(accion):
    global opciones_pendientes

    tipo = accion.get("accion")
    nombre_producto = accion.get("producto", "").strip().lower()

    # Datos comunes
    marca_txt = accion.get("marca")
    categoria_txt = accion.get("categoria")
    tipo_variedad = accion.get("tipo")
    contenido_valor = accion.get("contenido_valor")
    contenido_unidad = accion.get("contenido_unidad")
    alerta = accion.get("stock_alert")

    cantidad = normalizar_cantidad(accion.get("cantidad"))
    fecha_ingreso = normalizar_fecha(accion.get("fecha_ingreso"))
    fecha_caducidad = normalizar_fecha(accion.get("fecha_caducidad"))

    if not fecha_ingreso:
        fecha_ingreso = datetime.now().strftime("%Y-%m-%d")


    if tipo == "agregar":
        categoria = obtener_o_crear_categoria(categoria_txt)
        marca = obtener_o_crear_marca(marca_txt)

        producto = obtener_o_crear_producto(
            nombre_producto,
            marca,
            categoria,
            tipo_variedad,
            contenido_valor,
            contenido_unidad,
            alerta
        )

        # Crear lote
        lote = InventoryBatch(
            product_id=producto.id,
            quantity=cantidad,
            arrival_date=fecha_ingreso,
            expiration_date=fecha_caducidad
        )

        db.session.add(lote)
        db.session.commit()

        total = sum(l.quantity for l in producto.batches)

        return (
            f"Producto agregado correctamente.\n\n"
            f"Producto: {producto.name}\n"
            f"Marca: {marca.name}\n"
            f"Categoría: {categoria.name}\n"
            f"Tipo/Variedad: {producto.type_variety}\n"
            f"Contenido: {producto.content_value} {producto.content_unit}\n\n"
            f"Lote registrado:\n"
            f"- Cantidad: {cantidad}\n"
            f"- Ingreso: {fecha_ingreso}\n"
            f"- Caducidad: {fecha_caducidad or 'Sin fecha'}\n\n"
            f"Cantidad total disponible ahora: {total} unidades."
        )


    if tipo == "consultar":
        productos = Product.query.filter(Product.name.ilike(nombre_producto)).all()

        if not productos:
            return f"No tengo registros del producto '{nombre_producto}'."

        if len(productos) == 1:
            p = productos[0]
            lotes = InventoryBatch.query.filter_by(product_id=p.id).all()
            total = sum(l.quantity for l in lotes)

            respuesta = (
                f"Producto: {p.name}\n"
                f"Marca: {p.brand.name}\n"
                f"Categoría: {p.category.name}\n"
                f"Tipo/Variedad: {p.type_variety}\n"
                f"Contenido: {p.content_value} {p.content_unit}\n\n"
                f"Lotes disponibles:\n"
            )

            for i, l in enumerate(lotes, start=1):
                respuesta += (
                    f"{i}) Lote #{l.id}\n"
                    f"- Cantidad: {l.quantity}\n"
                    f"- Ingreso: {l.arrival_date}\n"
                    f"- Caducidad: {l.expiration_date or 'Sin fecha'}\n\n"
                )

            respuesta += f"Total disponible: {total} unidades."
            return respuesta

        # Si hay varios productos iguales (diferentes marcas o tipos)
        opciones_pendientes[nombre_producto] = productos

        respuesta = f"Se encontraron varias variantes de '{nombre_producto}':\n\n"

        for i, p in enumerate(productos, start=1):
            respuesta += (
                f"{i})\n"
                f"- Marca: {p.brand.name}\n"
                f"- Tipo/Variedad: {p.type_variety}\n"
                f"- Contenido: {p.content_value} {p.content_unit}\n\n"
            )

        respuesta += "Indica el número o una característica (por ejemplo: 'marca Mary')."
        return respuesta


    if tipo == "seleccionar":
        seleccion = accion.get("opcion", "").lower()

        if nombre_producto not in opciones_pendientes:
            return "No hay selección pendiente para ese producto."

        lista = opciones_pendientes[nombre_producto]

        # Selección por número
        if seleccion.isdigit():
            n = int(seleccion)
            if 1 <= n <= len(lista):
                elegido = lista[n - 1]
            else:
                return "Número inválido."
        else:
            # Selección por marca
            for p in lista:
                if p.brand.name.lower() in seleccion:
                    elegido = p
                    break
            else:
                return "No encontré coincidencias."

        del opciones_pendientes[nombre_producto]

        lotes = InventoryBatch.query.filter_by(product_id=elegido.id).all()
        total = sum(l.quantity for l in lotes)

        respuesta = (
            f"Producto seleccionado:\n\n"
            f"Producto: {elegido.name}\n"
            f"Marca: {elegido.brand.name}\n"
            f"Categoría: {elegido.category.name}\n"
            f"Tipo/Variedad: {elegido.type_variety}\n"
            f"Contenido: {elegido.content_value} {elegido.content_unit}\n\n"
            f"Lotes disponibles:\n"
        )

        for i, l in enumerate(lotes, start=1):
            respuesta += (
                f"{i}) Lote #{l.id}\n"
                f"- Cantidad: {l.quantity}\n"
                f"- Ingreso: {l.arrival_date}\n"
                f"- Caducidad: {l.expiration_date or 'Sin fecha'}\n\n"
            )

        respuesta += f"Total disponible: {total} unidades."
        return respuesta


    if tipo == "eliminar":
        productos = Product.query.filter(Product.name.ilike(nombre_producto)).all()

        if not productos:
            return f"No existe el producto '{nombre_producto}'."

        if len(productos) > 1:
            return "Hay varias variantes de este producto. Especifica marca o tipo."

        producto = productos[0]
        lotes = InventoryBatch.query.filter_by(product_id=producto.id).order_by(InventoryBatch.arrival_date.asc()).all()

        cantidad_a_eliminar = cantidad

        for lote in lotes:
            if cantidad_a_eliminar <= 0:
                break

            if lote.quantity <= cantidad_a_eliminar:
                cantidad_a_eliminar -= lote.quantity
                db.session.delete(lote)
            else:
                lote.quantity -= cantidad_a_eliminar
                cantidad_a_eliminar = 0

        db.session.commit()

        total = sum(l.quantity for l in producto.batches)

        if total == 0:
            db.session.delete(producto)
            db.session.commit()
            return f"Se eliminaron todas las unidades de '{nombre_producto}'. Producto eliminado."

        return f"Se eliminaron unidades. Cantidad restante total: {total}."


    if tipo == "editar":
        campo = accion.get("campo")
        valor = accion.get("valor")

        productos = Product.query.filter(Product.name.ilike(nombre_producto)).all()

        if not productos:
            return f"No existe el producto '{nombre_producto}'."

        if len(productos) > 1:
            return "Hay varias variantes de este producto. Especifica marca o tipo."

        producto = productos[0]

        if campo == "marca":
            marca = obtener_o_crear_marca(valor)
            producto.brand_id = marca.id

        elif campo == "categoria":
            categoria = obtener_o_crear_categoria(valor)
            producto.category_id = categoria.id

        elif campo == "tipo":
            producto.type_variety = valor

        elif campo == "contenido_valor":
            producto.content_value = float(valor)

        elif campo == "contenido_unidad":
            producto.content_unit = valor

        elif campo == "stock_alert":
            producto.stock_alert = int(valor)

        else:
            return f"El campo '{campo}' no es válido."

        db.session.commit()

        return f"El campo '{campo}' fue actualizado correctamente."

    return "No entendí tu solicitud."
