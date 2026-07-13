from datetime import datetime, date
from backend.models import db, Category, Brand, Product, ProductVariant, InventoryBatch

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


def generar_sku(producto, marca, tipo_variedad, contenido_valor, contenido_unidad):
    nombre = (producto.name or "").replace(" ", "").upper()
    marca_txt = (marca.name if marca else "SINMARCA").replace(" ", "").upper()
    variedad_txt = (tipo_variedad or "").replace(" ", "").upper()
    contenido_txt = ""
    if contenido_valor is not None and contenido_unidad:
        contenido_txt = f"{contenido_valor}{contenido_unidad}".upper()

    categoria_txt = "GEN"
    if producto.category:
        categoria_txt = producto.category.name.replace(" ", "").upper()

    return f"{categoria_txt}-{nombre}-{marca_txt}-{variedad_txt}-{contenido_txt}"


def obtener_o_crear_variante(producto, marca, tipo_variedad, contenido_valor, contenido_unidad):
    contenido_valor, contenido_unidad = normalizar_contenido(contenido_valor, contenido_unidad)

    tipo_variedad = tipo_variedad or ""

    variante = ProductVariant.query.filter_by(
        product_id=producto.id,
        brand_id=marca.id,
        content_value=contenido_valor,
        content_unit=contenido_unidad
    ).first()

    if not variante:
        sku = generar_sku(producto, marca, tipo_variedad, contenido_valor, contenido_unidad)
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
    else:
        variante.sku_code = generar_sku(producto, marca, tipo_variedad, contenido_valor, contenido_unidad)
        db.session.commit()

    return variante


def resolver_variante(target):
    nombre = target.get("product_name")
    marca = target.get("brand")
    categoria = target.get("category")
    variedad = target.get("type_variety")
    valor = target.get("content_value")
    unidad = target.get("content_unit")

    # 🔥 Validación mínima
    if not nombre:
        return None, "No se especificó el nombre del producto."

    # 🔥 Buscar producto por coincidencia parcial
    productos = Product.query.filter(Product.name.ilike(f"%{nombre}%")).all()
    if not productos:
        return None, "No existe el producto solicitado."

    # 🔥 Si hay varios productos, elegir el primero
    producto = productos[0]

    # 🔥 Obtener variantes del producto
    variantes = ProductVariant.query.filter_by(product_id=producto.id)

    # 🔥 Filtrar por marca SOLO si el usuario la mencionó
    if marca:
        marca_obj = Brand.query.filter(Brand.name.ilike(f"%{marca}%")).first()
        if not marca_obj:
            return None, "La marca indicada no existe."
        variantes = variantes.filter_by(brand_id=marca_obj.id)

    # 🔥 Filtrar por categoría SOLO si el usuario la mencionó
    if categoria:
        categoria_obj = Category.query.filter(Category.name.ilike(f"%{categoria}%")).first()
        if not categoria_obj:
            return None, "La categoría indicada no existe."
        variantes = variantes.filter_by(category_id=categoria_obj.id)

    # 🔥 Filtrar por variedad SOLO si el usuario la mencionó
    if variedad:
        variantes = variantes.filter(ProductVariant.type_variety.ilike(f"%{variedad}%"))

    # 🔥 Filtrar por contenido SOLO si el usuario lo mencionó
    if valor and unidad:
        variantes = variantes.filter_by(content_value=valor, content_unit=unidad)

    # 🔥 Obtener lista final
    variantes = variantes.all()

    if not variantes:
        return None, "No existe una variante que coincida con la descripción."

    # 🔥 Si hay varias variantes, elegir la más específica
    if len(variantes) > 1:
        # Preferir coincidencias exactas de contenido
        exactas = [
            v for v in variantes
            if (valor is None or v.content_value == valor)
            and (unidad is None or v.content_unit == unidad)
        ]
        if exactas:
            return exactas[0], None

    return variantes[0], None


def ejecutar_accion(contrato):

    lotes_huerfanos = InventoryBatch.query.filter_by(variant_id=None).all()
    if lotes_huerfanos:
        for lote in lotes_huerfanos:
            db.session.delete(lote)
        db.session.commit()

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

        contenido_valor, contenido_unidad = normalizar_contenido(contenido_valor, contenido_unidad)

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
            return f"No se encontró el producto o variante especificada. {error}"

        campo = changes.get("field")
        valor = changes.get("value")
        extra = changes.get("extra", {})
        batch_info = contrato.get("batch", {})

        if valor in ["Por definir", None, ""]:
            return "Necesito un valor para editar ese campo."

        nombre = variante.product.name
        marca = variante.brand.name if variante.brand else "Sin marca"
        variedad = variante.type_variety or "Sin variedad"
        contenido = (
            f"{variante.content_value} {variante.content_unit}"
            if variante.content_value else "Por definir"
        )

        valor_anterior = None
        regenerar_sku_flag = False

        if campo == "product_name":
            valor_anterior = nombre
            variante.product.name = valor
            regenerar_sku_flag = True

        elif campo == "category":
            valor_anterior = variante.product.category.name if variante.product.category else "General"
            nueva_categoria = obtener_o_crear_categoria(valor)
            variante.product.category_id = nueva_categoria.id
            regenerar_sku_flag = True

        elif campo == "brand":
            valor_anterior = marca
            nueva_marca = obtener_o_crear_marca(valor)
            variante.brand_id = nueva_marca.id
            regenerar_sku_flag = True

        elif campo == "type_variety":
            valor_anterior = variedad
            variante.type_variety = valor
            regenerar_sku_flag = True

        elif campo == "content_value":
            valor_anterior = contenido
            valor_num, unidad_norm = normalizar_contenido(valor, extra.get("content_unit", variante.content_unit))
            variante.content_value = valor_num
            variante.content_unit = unidad_norm
            regenerar_sku_flag = True

        elif campo == "content_unit":
            valor_anterior = contenido
            _, unidad_norm = normalizar_contenido(variante.content_value, valor)
            variante.content_unit = unidad_norm
            regenerar_sku_flag = True

        elif campo == "arrival_date":
            valor_anterior = "varía por lote"
            fecha_norm = normalizar_fecha(valor)
            for lote in variante.batches:
                lote.arrival_date = fecha_norm

        elif campo == "expiration_date":
            valor_anterior = "varía por lote"
            fecha_norm = normalizar_fecha(valor)
            for lote in variante.batches:
                lote.expiration_date = fecha_norm

        elif campo == "batch_quantity":
            lote_id = batch_info.get("batch_id")
            if not lote_id:
                return "Debes especificar el ID del lote que deseas editar."

            lote = InventoryBatch.query.get(lote_id)
            if not lote:
                return f"No existe el lote con ID {lote_id}."

            valor_anterior = lote.quantity
            lote.quantity += int(valor)

        else:
            return f"El campo '{campo}' no es válido."

        if regenerar_sku_flag:
            producto = variante.product
            marca_obj = variante.brand
            variante.sku_code = generar_sku(
                producto,
                marca_obj,
                variante.type_variety,
                variante.content_value,
                variante.content_unit
            )

        db.session.commit()

        return (
            f"El campo '{campo}' del producto '{nombre}' fue actualizado.\n"
            f"Valor anterior: {valor_anterior}\n"
            f"Nuevo valor: {valor}\n"
            f"SKU actual: {variante.sku_code}"
        )


    if action == "delete":
        variante, error = resolver_variante(target)
        if error:
            return f"No se encontró el producto o variante especificada. {error}"

        cantidad = normalizar_cantidad(batch.get("quantity"))
        lotes = InventoryBatch.query.filter_by(
            variant_id=variante.id
        ).order_by(InventoryBatch.arrival_date.asc()).all()

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

        nombre = variante.product.name
        marca = variante.brand.name if variante.brand else "Sin marca"
        variedad = variante.type_variety or "Sin variedad"
        contenido = (
            f"{variante.content_value} {variante.content_unit}"
            if variante.content_value else "Por definir"
        )

        if total == 0:
            db.session.delete(variante)
            db.session.commit()

            variantes_restantes = ProductVariant.query.filter_by(
                product_id=variante.product_id
            ).all()

            if len(variantes_restantes) == 0:
                producto = Product.query.get(variante.product_id)
                db.session.delete(producto)
                db.session.commit()

                return (
                    f"Se eliminaron todas las unidades de:\n"
                    f"- Producto: {nombre}\n"
                    f"- Marca: {marca}\n"
                    f"- Variedad: {variedad}\n"
                    f"- Contenido: {contenido}\n\n"
                    f"La variante y el producto fueron eliminados."
                )

            return (
                f"Se eliminaron todas las unidades de:\n"
                f"- Producto: {nombre}\n"
                f"- Marca: {marca}\n"
                f"- Variedad: {variedad}\n"
                f"- Contenido: {contenido}\n\n"
                f"La variante fue eliminada."
            )

        return (
            f"Eliminación completada para:\n"
            f"- Producto: {nombre}\n"
            f"- Marca: {marca}\n"
            f"- Variedad: {variedad}\n"
            f"- Contenido: {contenido}\n\n"
            f"Cantidad restante: {total}."
        )


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
