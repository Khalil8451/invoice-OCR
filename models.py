from sqlalchemy import ForeignKey
from .extensions import db
from sqlalchemy.orm import relationship
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    issuer = db.Column(db.String(50), nullable=False)
    date_invoice = db.Column(db.DateTime, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    invoice_number = db.Column(db.String(30), nullable=False)
    user_id = db.Column(
        db.Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    user = relationship('User', backref='Invoice')
