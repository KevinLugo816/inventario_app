from datetime import datetime, date
from models import db, Category, Brand, Product, ProductVariant, InventoryBatch

opciones_pendientes = {}

def normalizar_cantidad(valor):
    try:
        return int(valor)
    except:
        return 0


def normalizar_contenido(valor, unidad_raw):
    if valor in ["Por definir", None, ""]:
        return None, None

    try:
        v = float(valor)
    except:
        return None, None

    u = (unidad_raw or "").strip().lower()

    if u in ["litro", "litros", "l"]:
        return v, "L"
    if u in ["kg", "kilogramo", "kilogramos"]:
        return v, "kg"
    if u in ["gramo", "gramos", "g"]:
        return v, "g"
    if u in ["ml", "mililitro", "mililitros"]:
        return v, "ml"

    return v, unidad_raw


def normalizar_fecha(valor):
    if not valor or str(valor).lower() in ["-", "por definir", "none", "null"]:
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
    if not nombre or nombre == "Por definir":
        nombre = "General"

    cat = Category.query.filter_by(name=nombre).first()
    if not cat:
        cat = Category(name=nombre)
        db.session.add(cat)
        db.session.commit()
    return cat


def obtener_o_crear_marca(nombre):
    if not nombre or nombre == "Por definir":
        nombre = "Sin marca"

    marca = Brand.query.filter_by(name=nombre).first()
    if not marca:
        marca = Brand(name=nombre)
        db.session.add(marca)
        db.session.commit()
    return marca


def obtener_o_crear_producto(nombre, categoria):
    prod = Product.query.filter_by(name=nombre, category_id=categoria.id).first()
    if not prod:
        prod = Product(name=nombre, category_id=categoria.id)
        db.session.add(prod)
        db.session.commit()
    return prod


def obtener_o_crear_variante(producto, marca, tipo_variedad, contenido_valor, contenido_unidad):
    contenido_valor, contenido_unidad = normalizar_contenido(contenido_valor, contenido_unidad)

    variante = ProductVariant.query.filter_by(
        product_id=producto.id,
        brand_id=marca.id,
        type_variety=tipo_variedad,
        content_value=contenido_valor,
        content_unit=contenido_unidad
    ).first()

    if not variante:
        sku = f"{producto.name}-{marca.name}-{tipo_variedad}-{contenido_valor or ''}{contenido_unidad or ''}"
        variante = ProductVariant(
            product_id=producto.id,
            brand_id=marca.id,
            type_variety=tipo_variedad,
            content_value=contenido_valor,
            content_unit=contenido_unidad,
            sku_code=sku
        )
        db.session.add(variante)
        db.session.commit()

    return variante


def resolver_variante(target):
    nombre = (target.get("product_name") or "").lower()
    marca_txt = target.get("brand")
    variedad_txt = target.get("type_variety")
    valor = target.get("content_value")
    unidad = target.get("content_unit")

    # 1. Buscar producto base
    productos = Product.query.filter(Product.name.ilike(nombre)).all()
    if not productos:
        return None, "No existe el producto solicitado."

    # Si hay varios productos base, elegir el primero (normalmente no pasa)
    producto = productos[0]

    # 2. Buscar variantes del producto
    variantes = ProductVariant.query.filter_by(product_id=producto.id).all()

    # Filtrar por marca
    if marca_txt and marca_txt != "Por definir":
        variantes = [v for v in variantes if v.brand.name.lower() == marca_txt.lower()]

    # Filtrar por variedad
    if variedad_txt and variedad_txt != "Por definir":
        variantes = [v for v in variantes if (v.type_variety or "").lower() == variedad_txt.lower()]

    # Filtrar por contenido
    if valor not in ["Por definir", None] and unidad not in ["Por definir", None]:
        variantes = [
            v for v in variantes
            if v.content_value == float(valor) and v.content_unit == unidad
        ]

    if len(variantes) == 0:
        return None, "No existe una variante que coincida con la descripción."

    if len(variantes) > 1:
        return None, "Hay varias variantes. Especifica marca, variedad o contenido."

    return variantes[0], None


def ejecutar_accion(contrato):
    action = contrato.get("action")
    target = contrato.get("target", {})
    batch = contrato.get("batch", {})
    changes = contrato.get("changes", {})
    option = contrato.get("option")


    if action == "add":
        categoria = obtener_o_crear_categoria(target.get("category"))
        marca = obtener_o_crear_marca(target.get("brand"))
        producto = obtener_o_crear_producto(target.get("product_name"), categoria)

        contenido_valor = target.get("content_value")
        contenido_unidad = target.get("content_unit")

        if contenido_valor in ["Por definir", None, ""]:
            contenido_valor = None
        if contenido_unidad in ["Por definir", None, ""]:
            contenido_unidad = None

        variante = obtener_o_crear_variante(
            producto,
            marca,
            target.get("type_variety"),
            contenido_valor,
            contenido_unidad
        )

        arrival = normalizar_fecha(batch.get("arrival_date"))
        if not arrival:
            arrival = date.today().strftime("%Y-%m-%d")

        lote = InventoryBatch(
            variant_id=variante.id,
            quantity=normalizar_cantidad(batch.get("quantity")),
            arrival_date=arrival,
            expiration_date=normalizar_fecha(batch.get("expiration_date"))
        )

        db.session.add(lote)
        db.session.commit()

        return f"Producto agregado correctamente. SKU: {variante.sku_code}"


    if action == "query":
        variante, error = resolver_variante(target)
        if error:
            return error

        lotes = InventoryBatch.query.filter_by(variant_id=variante.id).all()
        total = sum(l.quantity for l in lotes)

        respuesta = (
            f"Producto: {variante.product.name}\n"
            f"Marca: {variante.brand.name}\n"
            f"Variedad: {variante.type_variety}\n"
            f"Contenido: {variante.content_value} {variante.content_unit}\n"
            f"SKU: {variante.sku_code}\n\n"
            f"Lotes:\n"
        )

        for l in lotes:
            respuesta += (
                f"- Lote #{l.id}: {l.quantity} unidades, "
                f"Ingreso: {l.arrival_date}, "
                f"Vence: {l.expiration_date or 'Sin fecha'}\n"
            )

        respuesta += f"\nTotal disponible: {total} unidades."
        return respuesta


    if action == "edit":
        variante, error = resolver_variante(target)
        if error:
            return error

        campo = changes.get("field")
        valor = changes.get("value")
        extra = changes.get("extra", {})

        if campo == "brand":
            marca = obtener_o_crear_marca(valor)
            variante.brand_id = marca.id

        elif campo == "type_variety":
            variante.type_variety = valor

        elif campo == "content_value":
            variante.content_value = float(valor)
            if "content_unit" in extra:
                variante.content_unit = extra["content_unit"]

        elif campo == "content_unit":
            variante.content_unit = valor

        elif campo == "arrival_date":
            for lote in variante.batches:
                lote.arrival_date = normalizar_fecha(valor)

        elif campo == "expiration_date":
            for lote in variante.batches:
                lote.expiration_date = normalizar_fecha(valor)

        else:
            return f"El campo '{campo}' no es válido."

        db.session.commit()
        return f"El campo '{campo}' fue actualizado correctamente."


    if action == "delete":
        variante, error = resolver_variante(target)
        if error:
            return error

        cantidad = normalizar_cantidad(batch.get("quantity"))
        lotes = InventoryBatch.query.filter_by(variant_id=variante.id).order_by(InventoryBatch.arrival_date.asc()).all()

        for lote in lotes:
            if cantidad <= 0:
                break

            if lote.quantity <= cantidad:
                cantidad -= lote.quantity
                db.session.delete(lote)
            else:
                lote.quantity -= cantidad
                cantidad = 0

        db.session.commit()

        total = sum(l.quantity for l in variante.batches)

        if total == 0:
            db.session.delete(variante)
            db.session.commit()

            variantes_restantes = ProductVariant.query.filter_by(product_id=variante.product_id).all()
            if len(variantes_restantes) == 0:
                producto = Product.query.get(variante.product_id)
                db.session.delete(producto)
                db.session.commit()
                return "Se eliminaron todas las unidades. Variante y producto eliminados."

            return "Se eliminaron todas las unidades. Variante eliminada."

        return f"Eliminación completada. Cantidad restante: {total}."


    if action == "select":
        clave = target.get("product_name")
        if clave not in opciones_pendientes:
            return "No hay selección pendiente."

        lista = opciones_pendientes[clave]

        if option.isdigit():
            idx = int(option)
            if 1 <= idx <= len(lista):
                variante = lista[idx - 1]
            else:
                return "Número inválido."
        else:
            variante = next((v for v in lista if option.lower() in v.sku_code.lower()), None)

        if not variante:
            return "No encontré coincidencias."

        del opciones_pendientes[clave]

        return f"Variante seleccionada: {variante.sku_code}"

    return "No entendí tu solicitud."
