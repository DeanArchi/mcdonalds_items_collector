import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/all_products')
def get_all_products():
    url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    menu_items = []

    for item in soup.find_all('li', class_='cmp-category__item'):
        item_id = item['data-product-id']
        name = item.find('div', class_='cmp-category__item-name').text.strip()

        menu_items.append({
            'id': item_id,
            'name': name,
        })

    with open('all_products.json', 'w', encoding='utf-8') as file:
        json.dump(menu_items, file, ensure_ascii=False, indent=4)

    data = app.response_class(
        response=json.dumps(menu_items, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

    return data


@app.route('/products/<int:product_name>')
def get_product(product_name):
    url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    item_description = []

    try:
        item = soup.find('li', {'data-product-id': f'{product_name}'})
        if item is None:
            raise ValueError(f"Item with id '{product_name} not found'")
    except ValueError as e:
        print(e)

    with webdriver.Chrome() as driver:
        wait = WebDriverWait(driver, 10)
        url = f'https://www.mcdonalds.com/ua/uk-ua/product/{product_name}.html'
        driver.get(url)
        time.sleep(10)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('span', class_='cmp-product-details-main__heading-title').text.strip()
        description = soup.find('span', class_='body').text.strip()
        item_dict = {
            'name': name,
            'description': description,
        }

        energy_value = soup.find_all('li', class_='cmp-nutrition-summary__heading-primary-item')
        for i, label in enumerate(['calories', 'fats', 'carbs', 'proteins']):
            value = energy_value[i].find('span', class_='').text.strip()
            item_dict.update({f'{label}': value})

        nutrient_content = soup.find_all('li', class_='label-item')
        for i, label in enumerate(['unsaturated_fats', 'sugar', 'salt', 'portion']):
            value = nutrient_content[i].find('span', class_='').text.strip().split()[0]
            item_dict.update({f'{label}': value})

        item_description.append(item_dict)

        with open('item_description.json', 'w', encoding='utf-8') as file:
            json.dump(item_description, file, ensure_ascii=False, indent=4)

        data = app.response_class(
            response=json.dumps(item_description, ensure_ascii=False, indent=4),
            status=200,
            mimetype='application/json'
        )

        return data


@app.route('/products/<product_name>/<product_field>')
def get_product_field(product_name, product_field):
    pass


if __name__ == '__main__':
    app.run()
