from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'  
    id = db.Column(db.Integer, primary_key=True)
    heading = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    product_url = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    
    def __init__(self, heading, category, product_url, name, price, image_url):
        self.heading = heading
        self.category = category
        self.product_url = product_url
        self.name = name
        self.price = price
        self.image_url = image_url
    
    def __repr__(self):
        return f"<Product id={self.id} name={self.name}>"
