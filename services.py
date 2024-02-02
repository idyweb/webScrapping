from requests_html import HTMLSession
from urllib.parse import urljoin
from flask import Flask, jsonify
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models import db, Product
import random
import time
import logging



links_dicts = [
        {"category_name": "women", "link": "https://www2.hm.com/en_gb/ladies.html", "link_suffix": "ladies"},
        {"category_name": "men", "link": "https://www2.hm.com/en_gb/men.html", "link_suffix": "men"},
        {"category_name": "divided", "link": "https://www2.hm.com/en_gb/divided.html", "link_suffix": "divided"},
        {"category_name": "baby", "link": "https://www2.hm.com/en_gb/baby.html", "link_suffix": "baby"},
        {"category_name": "kids", "link": "https://www2.hm.com/en_gb/kids.html", "link_suffix": "kids"},
        {"category_name": "h&m home", "link": "https://www2.hm.com/en_gb/home.html", "link_suffix": "home"},
        {"category_name": "beauty", "link": "https://www2.hm.com/en_gb/beauty.html", "link_suffix": "beauty"},
    ]


def scrape_and_store():
    session = HTMLSession()

    r = session.get('https://www2.hm.com/en_gb/index.html')

    categories = r.html.find('.CGae')
    result = {}

    for link_dict in links_dicts:
        urls = []
        for category in categories:
            try:
                links = category.find('a', first=True).attrs['href']
                if "https" not in links:
                    if links.split('/')[2] == link_dict.get("link_suffix"):
                        if links.split('/')[3] == "shop-by-product" or links.split('/')[3] == "products":
                            urls.append(links)
            except AttributeError:
                pass
        result[link_dict.get("category_name")] = urls
        
    return result


def scrape_products(category_name, url):
    session = HTMLSession()
    # products = []

    page = 1
    paginations = True

    while paginations:
        page_url = f"{url}?page={page}" if page > 1 else url
        print("page url", page_url)
        r = session.get(page_url)
        
        product_elements = r.html.find(".f0cf84")
        if not product_elements:
            paginations = False
            
        products = []
            
        for element in product_elements:
            item_url = element.find('.db7c79', first=True).attrs.get('href')
            product_name = element.find('.d1cd7b', first=True).text
            product_price = element.find('.aeecde', first=True).text
            heading = page_url.split("?")[0].split("/")[-1].replace(".html", "")
            img_element = element.find('.e357ce img', first=True)
            img_url = img_element.attrs.get('src') if img_element else None
            
            product = {"category_name": category_name, "products": heading, "product_url": item_url, "name": product_name, "price": product_price, "image_url": img_url}
            # products.append({"category_name": category_name, "products": heading, "product_url": item_url, "name": product_name, "price": product_price, "image_url": img_url})
            products.append(product)
        insert_into_db(products)
            
            
            
        page += 1
    # insert_into_db(products)


def insert_into_db(products):
    db_products = []

    for product in products:
        existing_product = Product.query.filter_by(product_url=product['product_url']).first()

        if not existing_product:
            db_product = Product(
                heading=product['products'],
                category=product['category_name'],
                product_url=product['product_url'],
                name=product['name'],
                price=product['price'],
                image_url=product['image_url']
            )
            db_products.append(db_product)

    if db_products:
        try:
            db.session.bulk_save_objects(db_products)
            db.session.commit()
            print("Bulk saved===>", len(db_products), "products")
        except Exception as e:
            db.session.rollback()
            print(f"Error bulk saving products: {e}")

        time.sleep(random.uniform(1, 3))


def get_a_name_for_this():

    result = scrape_and_store()
    
    for category_name, category_urls in result.items():
        category_prefix = next(link_dict['link'] for link_dict in links_dicts if link_dict['category_name'] == category_name)
        full_category_urls = [urljoin(category_prefix, url) for url in category_urls]
        
        for url in full_category_urls:
            try:
                scrape_products(category_name, url)
            except ConnectionResetError as e:
                print(f"ConnectionResetError: {e}. Retrying...")
                time.sleep(random.uniform(5, 10)) 
                continue
            except Exception as e:
                print(f"Error processing category {category_name}: {e}")