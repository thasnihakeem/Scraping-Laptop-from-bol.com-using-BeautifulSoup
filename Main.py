import time
import warnings
import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

warnings.filterwarnings('ignore')
driver = webdriver.Chrome(ChromeDriverManager().install())

def perform_request_with_retry(driver, url):
    MAX_RETRIES = 5
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            return extract_content(url)
        except:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                raise Exception("Request timed out")
            time.sleep(60)

def extract_content(url):
    driver.get(url)
    page_content = driver.page_source
    product_soup = BeautifulSoup(page_content, 'html.parser')
    dom = etree.HTML(str(product_soup))
    return dom

def scrape_product_urls(url):
    product_urls = []
    page_number = 1
    
    while True:
        dom = perform_request_with_retry(driver, url)
        all_items = dom.xpath('//a[contains(@class, "product-title")]/@href')
        for item in all_items:
            full_url = 'https://www.bol.com' + item
            product_urls.append(full_url)
            
        links_count = len(all_items)
        print(f"Scraped {links_count} links from page {page_number}")
        

        next_page = dom.xpath('//li[contains(@class, "pagination__controls--next")]/a/@href')
        if not next_page:
            break
        page_number += 1
        url = f'https://www.bol.com{next_page[0]}'
    
    print(f"Scraped a total of {len(product_urls)} product links")
    return product_urls

def get_product_name(dom):
    try:
        product_name = dom.xpath('//h1[@class="page-heading"]/span[@data-test="title"]/text()')[0].strip()
    except:
        product_name = 'Product name is not available'
    return product_name

def get_brand(dom):
    try:
        brand = dom.xpath('//div[contains(@class, "pdp-header__meta-item")][contains(text(), "Merk:")]/a/text()')[0].strip()
    except:
        brand = 'Brand is not available'
    return brand

def get_star_rating(dom):
    try:
        star_rating = dom.xpath('//div[@class="u-pl--xxs" and @data-test="rating-suffix"]/text()')[0]
        star_rating = star_rating.split('/')[0]  # Extract the first part before "/"
        star_rating = star_rating.replace(',', '.')  # Replace comma with dot
    except:
        star_rating = "Rating not available"
    return star_rating

def get_review_count(dom):
    try:
        review_count = dom.xpath('//div[@class="pdp-header__meta-item"]/wsp-scroll-to/a/div[@class="pdp-header__rating"]/div[@class="u-pl--xxs"]/text()')[0].strip()
        review_count = review_count.split('(')[1].split()[0]
    except:
        review_count = 'Review count is not available'
    return review_count

def get_product_image_url(dom):
    try:
        image_url = dom.xpath('//div[@class="image-slot"]/img/@src')[0]
    except:
        image_url = 'Product image URL is not available'
    return image_url

def get_sale_price(dom):
    try:
        sale_price = dom.xpath('//span[@class="promo-price"]/text()')[0]
        sale_price = sale_price.strip()  # Remove leading/trailing whitespace
    except:
        sale_price = "Sale price not available"
    return sale_price

def get_mrsp(dom):
    try:
        mrsp = dom.xpath('//div[contains(@class, "ab-discount")]/del[@data-test="list-price"]/text()')[0]
        mrsp = mrsp.strip()  # Remove leading/trailing spaces
    except:
        try:
            mrsp = dom.xpath('//span[@class="promo-price"]/text()')[0]
            mrsp = mrsp.strip()  # Remove leading/trailing spaces
        except:
            mrsp = "MRSP not available"
    return mrsp

def get_discount_percentage(dom):
    try:
        discount_percentage = dom.xpath('//div[contains(@class, "buy-block__discount")]/text()')[0].strip()
        discount_percentage = discount_percentage.replace('You save ', '')  # Remove "You save" prefix
    except:
        discount_percentage = "No discount"
    return discount_percentage

def get_stock_status(dom):
    try:
        stock_status = dom.xpath('//div[@class="buy-block__highlight u-mr--xxs" and @data-test="delivery-highlight"]/text()')[0].strip()
    except:
        try:
            stock_status = dom.xpath('//div[@class="buy-block__highlight--scarce buy-block__highlight"]/text()')[0].strip()
        except:
            stock_status = "Stock status not available"
    return stock_status

def get_pros_and_cons(dom):
    try:
        pros_cons_list = dom.xpath('//ul[@class="pros-cons-list"]/li/text()')
        pros_cons = '\n'.join([item.strip() for item in pros_cons_list])
    except:
        pros_cons = "Pros and cons not available"
    return pros_cons

def get_product_description(dom):
    try:
        description_element = dom.xpath('//section[@class="slot slot--description slot--seperated slot--seperated--has-more-content js_slot-description"]//div[@class="js_description_content js_show-more-content"]/div[@data-test="description"]')[0]
        product_description = description_element.xpath('string()').strip()
    except:
        product_description = "Product description not available"
    return product_description


def get_product_specifications(dom):
    specifications = {}
    try:
        specs_element = dom.xpath('//section[@class="slot slot--seperated slot--seperated--has-more-content js_slot-specifications"]')[0]
        specs_rows = specs_element.xpath('.//div[@class="specs__row"]')
        for row in specs_rows:
            title_element = row.xpath('.//dt[@class="specs__title"]')[0]
            title = title_element.xpath('normalize-space()')
            title = title.split("Tooltip")[0].strip()
            value_element = row.xpath('.//dd[@class="specs__value"]')[0]
            value = value_element.xpath('normalize-space()')
            specifications[title] = value
    except:
        return {}

    return specifications


def main():
    url = 'https://www.bol.com/nl/nl/l/laptops/4770/'
    product_links = scrape_product_urls(url)

    data = []
    for i, link in enumerate(product_links):
        dom = perform_request_with_retry(driver, link)
        product_name = get_product_name(dom)
        brand = get_brand(dom)
        image = get_product_image_url(dom)
        star_rating = get_star_rating(dom)
        review_count = get_review_count(dom)
        sale_price = get_sale_price(dom)
        mrp = get_mrsp(dom)
        discount = get_discount_percentage(dom)
        stock_status = get_stock_status(dom)
        pros_and_cons = get_pros_and_cons(dom)
        product_description = get_product_description(dom)
        product_specifications = get_product_specifications(dom)
        
        data.append({'product_url': link, 'product_name': product_name, 'image': image, 'rating': star_rating,
                     'no_of_reviews': review_count, 'mrp': mrp, 'sale_price': sale_price, 'discount': discount,
                     'stock_status': stock_status, 'pros_and_cons': pros_and_cons, 'product_description': product_description,
                     'product_specifications': product_specifications})

        if i % 10 == 0 and i > 0:
            print(f"Processed {i} links.")

        if i == len(product_links) - 1:
            print(f"All information for {i + 1} links has been scraped.")

    df = pd.DataFrame(data)
    df.to_csv('product_data.csv')
    print('CSV file has been written successfully.')
    driver.close()


if __name__ == '__main__':
    main()

