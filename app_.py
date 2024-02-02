from flask import Flask, jsonify, request 
from flask_migrate import Migrate
from models import db, Product

from services import get_a_name_for_this


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://mmwxlvje:elrFIExzl2OOXI1K0k8hyKJe-9wt_CwR@salt.db.elephantsql.com/mmwxlvje"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 20 
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/scrape_and_store', methods=['GET'])
def scrape_site():
    get_a_name_for_this()
    return jsonify({'message': 'Scraping and storing completed successfully'}), 200

@app.route('/products', methods=['GET'])
def get_products_by_heading():
    heading = request.args.get('heading')
    
    if not heading:
        return jsonify({'error': 'Heading is required in the query parameters'}), 400

    products = Product.query.filter_by(heading=heading).all()
    
    if not products:
        return jsonify({'message': 'No products found for the given category'}), 404

    serialized_products = [{
        'category_name': product.category,
        'products': product.heading,
        'product_url': product.product_url,
        'name': product.name,
        'price': product.price,
        'image_url': product.image_url
    } for product in products]

    return jsonify({'products': serialized_products}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)