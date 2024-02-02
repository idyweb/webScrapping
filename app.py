from requests_html import HTMLSession
from urllib.parse import urljoin
from flask import Flask, jsonify
from flask_migrate import Migrate
from models import db, Product
import random
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://mmwxlvje:elrFIExzl2OOXI1K0k8hyKJe-9wt_CwR@salt.db.elephantsql.com/mmwxlvje"
app.config['SQLALCHEMY_POOL_SIZE'] = 20 
db.init_app(app)
migrate = Migrate(app, db)

# session = HTMLSession()

# r = session.get('https://www2.hm.com/en_gb/index.html')

@app.route('/scrape_and_store', methods=['GET'])
def scrape_and_store():
    session = HTMLSession()

    r = session.get('https://www2.hm.com/en_gb/index.html')

    links_dicts = [
        {"category_name": "women", "link": "https://www2.hm.com/en_gb/ladies.html", "link_suffix": "ladies"},
    ]

    categories = r.html.find('.CGae')
    result = {}

    for link_dict in links_dicts:
        urls = []
        for category in categories:
            try:
                name = category.text
                links = category.find('a', first=True).attrs['href']
                if "https" not in links:
                    if links.split('/')[2] == link_dict.get("link_suffix"):
                        if links.split('/')[3] == "shop-by-product" or links.split('/')[3] == "products":
                            urls.append(links)
            except AttributeError:
                pass
        result[link_dict.get("category_name")] = urls

    def scrape_products(category_name, url):
        
        session = HTMLSession()
        r = session.get(url)
        products = []
        
        heading = url.split('/')[-1].replace('.html', '')
        
        offset = 0
        page_size = 36
        
        while True:
            page_url = f"{url}?sort=stock&image-size=small&image=model&offset={offset}&page-size={page_size}"
            r = session.get(page_url)

            product_elements = r.html.find(".product-item")
            if not product_elements:
                break
            
            for element in product_elements:
                item_url = element.find('.link', first=True).attrs.get('href')
                if item_url and not item_url.startswith(('http://', 'https://')):
                    item_url = urljoin(url, item_url)
                product_page = session.get(item_url)
                heading_element = product_page.html.find('.heading', first=True)
                heading = heading_element.text.strip() if heading_element and heading_element.text else None

                product_name = element.find('.item-heading', first=True).text
                product_price = element.find('.price', first=True).text
                img_url = element.find('.image-container img.item-image', first=True).attrs.get('src') or element.find('.image-container img.item-image', first=True).attrs.get('data-src') or element.find('.image-container img.item-image', first=True).attrs.get('data-altimage')
                products.append({"category_name": category_name, "products": heading, "product_url": item_url, "name": product_name, "price": product_price, "image_url": img_url})

            offset += page_size
            page_size = 72 
        return products

    for category_name, category_urls in result.items():
        print(f"\nCategory: {category_name}")
        category_prefix = next(link_dict['link'] for link_dict in links_dicts if link_dict['category_name'] == category_name)
        full_category_urls = [urljoin(category_prefix, url) for url in category_urls]

        for url in full_category_urls:
            print(f"Processing URL: {url}")
            try:
                products = scrape_products(category_name, url)
                print(f"Scraped {len(products)} products")
                for product in products:
                    
                    existing_product = Product.query.filter_by(product_url=product['product_url']).first()
                    
                    if existing_product:
                        pass
                    else:
                        # Store the scraped data in the database
                #         db_product = Product(
                #             heading=product['products'],
                #             category=product['category_name'],
                #             product_url=product['product_url'],
                #             name=product['name'],
                #             price=product['price'],
                #             image_url=product['image_url']
                #         )
                #         db.session.add(db_product)

                # db.session.commit()
                        print(product)

                time.sleep(random.uniform(1, 3)) 
            except ConnectionResetError as e:
                print(f"ConnectionResetError: {e}. Retrying...")
                time.sleep(random.uniform(5, 10)) 
                continue
            except Exception as e:
                print(f"Error processing category {category_name}: {e}")
                
    return jsonify({'message': 'Scraping and storing completed successfully'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)