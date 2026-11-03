import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# 1. Define the Target (Input)
BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
# We will scrape the first 3 pages as a test
PAGES_TO_SCRAPE = 3 

# 2. The Mechanism (The Scraper)
def scrape_books():
    all_books = []
    
    for page_num in range(1, PAGES_TO_SCRAPE + 1):
        url = BASE_URL.format(page_num)
        print(f"Crawling: {url}")
        
        # Fetch the HTML
        response = requests.get(url)
        
        # Check if the connection was successful (Status 200 means OK)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page_num}")
            continue
            
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all book containers on the page
        books = soup.find_all('article', class_='product_pod')
        
        for book in books:
            # Extract the title (found inside the <h3> -> <a> -> title attribute)
            title = book.h3.a['title']
            
            # Extract the price (found inside <p class="price_color">)
            price = book.find('p', class_='price_color').text
            
            # Extract availability (found inside <p class="instock availability">)
            availability = book.find('p', class_='instock availability').text.strip()
            
            # Store it in a dictionary
            all_books.append({
                'title': title,
                'price': price,
                'availability': availability
            })
            
        # Be polite to the server. Wait 1 second between requests to avoid getting blocked.
        time.sleep(1)
        
    return all_books

# 3. The Output (Storage)
if __name__ == "__main__":
    print("Starting the crawler...")
    extracted_data = scrape_books()
    
    # Convert our list of dictionaries into a Pandas DataFrame
    df = pd.DataFrame(extracted_data)
    
    # Ensure the data directory exists
    os.makedirs('raw_data', exist_ok=True)
    
    # Save to a CSV file (This is our unstructured data becoming semi-structured)
    output_path = 'raw_data/books_raw.csv'
    df.to_csv(output_path, index=False)
    
    print(f"Success! Extracted {len(df)} records.")
    print(f"Data saved to {output_path}")
