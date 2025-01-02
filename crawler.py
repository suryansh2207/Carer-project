import requests
from bs4 import BeautifulSoup
import mysql.connector
import configparser
from datetime import datetime
from typing import Optional, Dict
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> configparser.ConfigParser: #This function helps us to load the configuration file
    """Load configuration from config.in file"""
    config = configparser.ConfigParser()
    config.read('config.in')
    return config

def connect_db(): #This function helps us to connect to the database
    """Establish MySQL database connection"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='22072003',
        database='articles_db'
    )

def extract_article_data(url: str) -> Optional[Dict[str, str]]: #This function helps us to extract the article data from the URL we provide
    """Extract article details from given URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {url} with status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1', class_='c-article-title')
        title_text = title.text.strip() if title else "N/A"

        # Extract authors
        authors = []
        author_list = soup.find('ul', class_='c-article-author-list')
        if author_list:
            for li in author_list.find_all('li', class_='c-article-author-list__item'):
                # Find the <a> tag with the data-test="author-name"
                author_tag = li.find('a', {'data-test': 'author-name'})
                if author_tag:
                    authors.append(author_tag.text.strip())

        # Join authors into a single string
        authors_text = ', '.join(authors) if authors else "N/A"

        # Extract publication date
        time_element = soup.find('time')
        pub_date = time_element['datetime'] if time_element else "N/A"

        # Extract abstract
        abstract = soup.find('div', class_='c-article-section__content c-article-section__content--standfirst u-text-bold')
        abstract_text = abstract.text.strip() if abstract else "N/A"

        article_data = {
            'title': title_text,
            'authors': authors_text,
            'pub_date': pub_date,
            'abstract': abstract_text,
        }

        logger.info(f"Extracted data: {article_data}")
        return article_data

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return None

def store_article(db_conn, article_data: Dict[str, str]) -> Optional[int]: #This function helps us to store the article data in the MySQL database
    """Store article data in MySQL database"""
    cursor = db_conn.cursor()
    try:
        query = """
        INSERT INTO articles (title, authors, pub_date, abstract)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            article_data['title'],
            article_data['authors'],
            article_data['pub_date'],
            article_data['abstract']
        ))
        db_conn.commit()
        logger.info(f"Stored article: {article_data['title']}")
        return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error storing article: {str(e)}")
        db_conn.rollback()
        return None
    finally:
        cursor.close()

def fetch_articles(): #This function helps us to fetch the articles from the URL we provide
    """Main function to crawl and store articles"""
    config = load_config()
    base_url = config['crawler']['base_url']
    
    try:
        response = requests.get(base_url, timeout=10)
        logger.info(f"Fetched URL: {base_url} with status code: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article links
        article_links = soup.find_all('a', href=True, class_='u-link-inherit')
        
        if not article_links:
            logger.info("No article links found on the page.")
        else:
            logger.info(f"Found {len(article_links)} article links.")
        
        db_conn = connect_db()
        
        for link in article_links:
            relative_url = link['href']
            url = urljoin(base_url, relative_url)  # Construct the full URL
            logger.info(f"Processing article URL: {url}")
            article_data = extract_article_data(url)
            if article_data:
                store_article(db_conn, article_data)
                
    except Exception as e:
        logger.error(f"Error in fetch_articles: {str(e)}")
    finally:
        if 'db_conn' in locals():
            db_conn.close()

