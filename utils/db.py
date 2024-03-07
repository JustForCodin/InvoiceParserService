from flask_sqlalchemy import SQLAlchemy
from services.invoice_parser import app

_db = SQLAlchemy()

class Customer(_db.Model):
    CustomerID = _db.Column(_db.Integer, primary_key=True)
    FullName = _db.Column(_db.String(100), nullable=False)
    Email = _db.Column(_db.String(100), unique=True, nullable=False)
    Password = _db.Column(_db.String(100), nullable=False)
    invoices = _db.relationship('Invoice', backref='customer', lazy=True)


class Invoice(_db.Model):
    InvoiceID = _db.Column(_db.Integer, primary_key=True)
    CustomerID = _db.Column(_db.Integer, _db.ForeignKey('customer.CustomerID'), nullable=False)
    BillFrom = _db.Column(_db.String(100), nullable=False)
    BillTo = _db.Column(_db.String(100), nullable=False)
    InvoiceDate = _db.Column(_db.Date)
    DueDate = _db.Column(_db.Date)
    items = _db.relationship('InvoiceItem', backref='invoice', lazy=True)


class InvoiceItem(_db.Model):
    __tablename__ = "InvoiceItem"
    ItemID = _db.Column(_db.Integer, primary_key=True)
    InvoiceID = _db.Column(_db.Integer, _db.ForeignKey('invoice.InvoiceID'), nullable=False)
    ItemDescription = _db.Column(_db.Text)
    UnitPrice = _db.Column(_db.Numeric(10, 2))
    Quantity = _db.Column(_db.Integer)
    LineTotal = _db.Column(_db.Numeric(10, 2))
