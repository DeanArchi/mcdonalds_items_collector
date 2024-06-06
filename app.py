import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
from flask import Flask
import requests
from bs4 import BeautifulSoup
from transliterate import translit
import re

app = Flask(__name__)


def get_product_info(product_name):
    """
    This function is designed to retrieve product information by product name. It searches for the specified product
    on the menu page, extracts product information such as name, description, and characteristics, and returns this
    information in the form of a dictionary. If the product is not found, an empty list is returned.
    """
    url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
    response = requests.get(url)
    # get html from main page
    soup = BeautifulSoup(response.text, 'html.parser')
    item_description = []
    product_id = 0

    # find all products of the menu
    menu_elements = soup.find_all('li', class_='cmp-category__item')
    for item in menu_elements:
        item_name = item.find('div', class_='cmp-category__item-name').text.strip()
        # transliterate name of the product. For example, Роял Делюкс - rojal-deljuks
        item_name_translit = translit(item_name, 'uk', reversed=True)
        formatted_item_name_translit = re.sub(r'\W+', '-', item_name_translit.lower()).rstrip('-')

        if formatted_item_name_translit == product_name:
            product_id = item.get('data-product-id')
            break

    if not product_id:
        return 'Product not found', 404

    # opening a page with detailed product information using Selenium, since the data on this page
    # is generated dynamically
    with webdriver.Chrome() as driver:
        wait = WebDriverWait(driver, 10)
        url = f'https://www.mcdonalds.com/ua/uk-ua/product/{product_id}.html'
        driver.get(url)
        time.sleep(10)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

    #   writing all the necessary fields such as:
        #   name
        #   description
        #   calories
        #   fats
        #   carbs
        #   proteins
        #   unsaturated fats
        #   sugar
        #   salt
        #   portion
    #   to a variable 'item_description'
        name = soup.find('span', class_='cmp-product-details-main__heading-title').text.strip()
        description = soup.find('div', class_='cmp-text').text.strip()
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

    return item_description


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/all_products')
def get_all_products():
    """
    This get_all_products function gets a list of all products from a menu and returns them in JSON format.
    It goes to the McDonald's menu web page, parses the HTML code, finds all the items in the list of products,
    and stores the information about each product (its ID and name) in a Python dictionary. It then writes this
    list to a JSON file and returns it in a JSON response to the server with an HTTP status of 200 (OK).
    """
    url = 'https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html'
    response = requests.get(url)
    # get html from main page
    soup = BeautifulSoup(response.text, 'html.parser')

    menu_items = []

    # finding names and id of all products
    for item in soup.find_all('li', class_='cmp-category__item'):
        item_id = item['data-product-id']
        name = item.find('div', class_='cmp-category__item-name').text.strip()

        menu_items.append({
            'id': item_id,
            'name': name,
        })

    # writing to a json file
    with open('all_products.json', 'w', encoding='utf-8') as file:
        json.dump(menu_items, file, ensure_ascii=False, indent=4)

    # return information in json format
    data = app.response_class(
        response=json.dumps(menu_items, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

    return data, 200


@app.route('/products/<string:product_name>')
def get_product(product_name):
    """
    This function responds to user requests at “/products/<product_name>”. It calls the get_product_info function
    to get information about the product by the specified name. The received information is written to the
    “item_description.json” file in JSON format. After that, the function generates an HTTP response with a JSON
    representation of the product information and returns it with an HTTP status of 200 (OK).

    Here's a list of transliterated product names for testing functionality:
    For exmaple: /products/makfluri-kit-kat-karamel
    makpyrih-polunytsja
    rojal-deljuks
    bih-mak
    chizburher
    chiken-maknahets-4sht
    syr-kamamber
    ketchup
    maksandi-shokolad-u-plastykovomu-stakanchyku
    makpyrih-vyshnevyj
    """

    # retrieve product information using the helper function
    product_info = get_product_info(product_name)

    # return information in json format
    data = app.response_class(
        response=json.dumps(product_info, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

    return data, 200


@app.route('/products/<string:product_name>/<string:product_field>')
def get_product_field(product_name, product_field):
    """
    This function retrieves information about a specific product field from the McDonald's menu.
    If the product is found, the function searches for the required field and returns its value in JSON format.

    To test this feature, use the list of transliterated product names above.
    For exmaple: /products/makfluri-kit-kat-karamel/description
                 /products/makfluri-kit-kat-karamel/calories
    """
    # initialize an empty list to store the field description
    product_field_description = []
    # retrieve product information using the helper function
    product_info = get_product_info(product_name)

    # check if the product information was found
    if product_info:
        # select 0 element, since product_info is a list with 1 element
        product = product_info[0]
        # check if the requested field exists in the product information
        if product_field in product:
            field_value = product[product_field]
            # add the field and its value to the description list
            product_field_description.append({
                f'{product_field}': field_value,
            })
            # writing to a json file
            with open('item_field.json', 'w', encoding='utf-8') as file:
                json.dump(product_field_description, file, ensure_ascii=False, indent=4)

            # return information in json format
            data = app.response_class(
                response=json.dumps(product_field_description, ensure_ascii=False, indent=4),
                status=200,
                mimetype='application/json'
            )
            return data, 200
        else:
            return f"Field '{product_field}' not found", 404
    else:
        return f"Product '{product_name}' not found", 404


if __name__ == '__main__':
    app.run(debug=True)
