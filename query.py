import mysql.connector
from datetime import datetime, timedelta
import logging
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection
from typing import List, Dict
import configparser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> dict: 
    """Load configuration from config.in file"""
    config = configparser.ConfigParser()
    config.read('config.in')
    return config

def connect_db():
    """Establish MySQL database connection"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='22072003',
        database='articles_db'
    )

def search_articles(query_text: str) -> List[Dict]: #This function helps us to search articles based on the query text
    """Search articles based on query text"""
    config = load_config()
    db_conn = connect_db()
    
    try:
        if 'last week' in query_text.lower():
            cursor = db_conn.cursor(dictionary=True)
            last_week = datetime.now() - timedelta(days=7)
            cursor.execute(
                "SELECT * FROM articles WHERE pub_date >= %s",
                (last_week.strftime('%Y-%m-%d'),)
            )
            results = cursor.fetchall()
            cursor.close()
            return results
        
        # Vector similarity search
        connections.connect(
            host='localhost',
            port='19530'
        )
        
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        query_vector = model.encode([query_text])[0]
        
        collection = Collection(config['milvus']['collection_name'])
        collection.load()
        
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="title_vector",
            param=search_params,
            limit=5
        )
        
        cursor = db_conn.cursor(dictionary=True)
        ids = [str(hit.id) for hit in results[0]]
        cursor.execute(
            f"SELECT * FROM articles WHERE id IN ({','.join(ids)})"
        )
        results = cursor.fetchall()
        cursor.close()
        logger.info(f"Search results for '{query_text}':")
        for result in results:
            logger.info(result)
    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        return []
    finally:
        db_conn.close()


if __name__ == "__main__":
    query_text = "Give me the journal those are published last week"
    articles = search_articles(query_text)
    for article in articles:
        print(article)