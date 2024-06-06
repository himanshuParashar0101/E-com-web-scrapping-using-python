import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import sqlite3
import time
from fuzzywuzzy import fuzz


# Returns list of {name, price} pairs
def scrape_reliance(search_url):
    print("Going to url: ", search_url)
    headers = {
        'User-Agent': ''
    }
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve the webpage")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []

    for product in soup.find_all('div', {'class': 'sp__product'}):
        name_tag = product.find('p', {'class': 'sp__name'})
        price_tags = product.find_all('span', {'class': 'TextWeb__Text-sc-1cyx778-0'})
        price_tag = ''
        for pt in price_tags:
            if pt.text and pt.text.strip()[0] == '₹':
                price_tag = pt
                break

        if name_tag and price_tag:
            name = name_tag.text.strip()
            price = price_tag.text.strip()
            results.append({'name': name, 'price': price})
    
    return results

# Returns list of {name, price} pairs
def scrape_flipkart(search_url):
    print("Going to url: ", search_url)
    headers = {
        'User-Agent': '*',
    }
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve the webpage")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []

    for product in soup.find_all('div', {'class': '_75nlfW'}):
        name_tag = product.find('div', {'class': 'KzDlHZ'})
        if name_tag == None:
            name_tags = product.find_all('a')
            name_tag = name_tags[1]
        price_tag = product.find('div', {'class': 'Nx9bqj'})
        
        if name_tag and price_tag:
            name = name_tag.text.strip()
            price = price_tag.text.strip()
            results.append({'name': name, 'price': price})
    
    return results


# Will match similar Products from Reliance and Flipkart based on name. Uses fuzzywuzzy library
def match_and_compare(data1, data2):
    matched_data = []
    used_indices = set()

    for product1 in data1:
        best_match = None
        best_score = 0
        best_index = None
        
        for i, product2 in enumerate(data2):
            if i in used_indices:
                continue
            
            score = fuzz.partial_ratio(product1['name'], product2['name'])
            if score > best_score:
                best_match = product2
                best_score = score
                best_index = i
        
        if best_match and best_score >= 30:             # Similarity threshold set to 30%
            matched_data.append((product1, best_match))
            used_indices.add(best_index)

    return matched_data


# Will create a bar graph to visualize prices of product on Reliance and Flipkart
def visualize_data(matched_data):

    reliance_prices = [int(pair[0]['price'].replace('₹', '').replace(',', '').split('.')[0]) if pair[0]['price'] else 0 for pair in matched_data]
    flipkart_prices = [int(pair[1]['price'].replace('₹', '').replace(',', '').split('.')[0]) if pair[1]['price'] else 0 for pair in matched_data]

    x_labels = [f"{pair[0]['name']}\n{pair[1]['name']}" for pair in matched_data]

    x = range(len(matched_data))

    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = 0.35
    bar1 = ax.bar(x, reliance_prices, bar_width, label='Reliance Digital', color='blue')
    bar2 = ax.bar([i + bar_width for i in x], flipkart_prices, bar_width, label='Flipkart', color='orange')

    ax.set_xlabel('Product Names')
    ax.set_ylabel('Price (INR)')
    ax.set_title('Price Comparison of Products from Reliance Digital and Flipkart')
    ax.set_xticks([i + bar_width / 2 for i in x])
    ax.set_xticklabels(x_labels)
    ax.legend()

    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.show()


# Will create an sqlite3 db and store reliance and flipkart products in separate tables
def store_in_database(data1, data2):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS reliance
                 (name TEXT, price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flipkart
                 (name TEXT, price REAL)''')

    for product in data1:
        c.execute("INSERT INTO reliance VALUES (?, ?)", (product['name'], product['price']))

    for product in data2:
        c.execute("INSERT INTO flipkart VALUES (?, ?)", (product['name'], product['price']))

    conn.commit()
    conn.close()


def main():
    print("  This script Compares prices between Reliance Digital and Flipkart")
    print("*********************************************************************\n")

    searchQuery = input('Enter Search Query (Leave Blank for default: "voltas air conditioner 1.5 ton split"): ')
    searchQuery = "voltas air conditioner 1.5 ton split" if searchQuery == "" else searchQuery

    relianceQuery = searchQuery.replace(' ', '%20')
    flipkartQuery = searchQuery.replace(' ', '%20')

    reliance = scrape_reliance(f'https://www.reliancedigital.in/search?q={relianceQuery}:relevance')    # List of pairs of 'name' and 'price'
    flipkart = scrape_flipkart(f'https://www.flipkart.com/search?q={flipkartQuery}')

    print(reliance)
    print("********************************************************")
    print(flipkart)

    matched_data = match_and_compare(reliance[:5], flipkart[:5])       # It will match mox 5 products

    store_in_database(reliance, flipkart)

    visualize_data(matched_data)

if __name__ == '__main__':
    main()