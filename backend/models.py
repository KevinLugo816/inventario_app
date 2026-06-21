from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

# -----------------------------
# Tabla de Rubros / Categorías
# -----------------------------
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)


# -----------------------------
# Tabla de Marcas
# -----------------------------
class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    products = db.relationship("Product", backref="brand", lazy=True)


# -----------------------------
# Tabla de Productos (Catálogo Maestro)
# -----------------------------
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(120), nullable=True)

    name = db.Column(db.String(200), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False)

    type_variety = db.Column(db.String(200), nullable=True)

    content_value = db.Column(db.Float, nullable=True)
    content_unit = db.Column(db.String(20), nullable=True)

    stock_alert = db.Column(db.Integer, nullable=True)

    batches = db.relationship("InventoryBatch", backref="product", lazy=True)


# -----------------------------
# Tabla de Lotes / Ingresos
# -----------------------------
class InventoryBatch(db.Model):
    __tablename__ = "inventory_batches"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    arrival_date = db.Column(db.Date, nullable=False, default=date.today)
    expiration_date = db.Column(db.Date, nullable=True)
