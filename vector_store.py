from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
from typing import List
import logging
from crawler import connect_db, load_config

logger = logging.getLogger(__name__)

def init_vector_store(): #This function helps us to initialize the vector store
    """Initialize Milvus connection and create collection"""
    config = load_config()
    try:
        connections.connect(
            host=config['milvus']['host'],
            port=int(config['milvus']['port'])
        )
        
        collection_name = config['milvus']['collection_name']
        if not utility.has_collection(collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                FieldSchema(name="title_vector", dtype=DataType.FLOAT_VECTOR, dim=384)
            ]
            schema = CollectionSchema(fields, collection_name)
            Collection(name=collection_name, schema=schema)
            logger.info(f"Collection '{collection_name}' created successfully.")
        else:
            logger.info(f"Collection '{collection_name}' already exists.")
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        raise

def store_vectors(titles: List[str], ids: List[int]): #This function helps us to store the vectors in Milvus
    """Store title vectors in Milvus"""
    config = load_config()
    try:
        # Input validation
        if not titles or not ids:
            raise ValueError("Empty titles or ids provided")
        if len(titles) != len(ids):
            raise ValueError("Number of titles and ids must match")

        # Generate vectors
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        vectors = model.encode(titles)

        # Create entities matching the schema field names
        entities = [
            {
                "id": id_val,
                "title_vector": vector.tolist()  # Changed to match schema field name
            }
            for id_val, vector in zip(ids, vectors)
        ]

        collection = Collection(config['milvus']['collection_name'])
        collection.insert(entities)
        collection.flush()

        # Create an index for the title_vector field
        index_params = {
            "index_type": "IVF_FLAT",  # Choose the index type appropriate for your use case
            "params": {"nlist": 128},  # Example parameter, adjust as needed
            "metric_type": "L2"  # Or "IP" for inner product, depending on your requirements
        }
        collection.create_index(field_name="title_vector", index_params=index_params)

        logger.info(f"Successfully stored {len(entities)} vectors and created an index")
    except Exception as e:
        logger.error(f"Error storing vectors: {str(e)}")
        raise


def verify_stored_vectors(collection: Collection, ids: List[int]): #This function helps us to verify the stored vectors
    """Verify that vectors are stored correctly in Milvus"""
    try:
        # Load the collection into memory
        collection = Collection("article_vectors")
        collection.load()
        
        for id_val in ids:
            # Use '==' for equality check
            expr = f"id == {id_val}"  
            results = collection.query(expr=expr)
            if not results:
                logger.warning(f"No vector found for ID: {id_val}")
            else:
                logger.info(f"Vector found for ID: {id_val}")
    except Exception as e:
        logger.error(f"Error verifying stored vectors: {str(e)}")


def process_articles(): #This function helps us to process the articles
    """Process and store vectors for all articles"""
    db_conn = connect_db()
    try:
        cursor = db_conn.cursor(dictionary=True)
        
        # Add logging before query
        logger.debug("Executing database query...")

        cursor.execute("SELECT id, title FROM articles")
        articles = cursor.fetchall()

        # Add logging after fetch
        logger.debug(f"Number of articles fetched: {len(articles)}")
        if not articles:
            logger.error("No articles found in database")
            return
            
        # Log first few articles for debugging
        logger.debug(f"First few articles: {articles[:3]}")

        titles = [article['title'] for article in articles]
        ids = [article['id'] for article in articles]

        # Log extracted data
        logger.debug(f"Number of titles extracted: {len(titles)}")
        logger.debug(f"Number of ids extracted: {len(ids)}")

        store_vectors(titles, ids)
    except Exception as e:
        logger.error(f"Error in process_articles: {str(e)}")
        raise
    finally:
        cursor.close()
        db_conn.close()

def search_vectors(query_title: str): #This function helps us to search for similar vectors based on a query title
    """Search for similar vectors based on a query title"""
    config = load_config()
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        query_vector = model.encode([query_title]).tolist()

        collection = Collection(config['milvus']['collection_name'])
        search_params = {
            "metric_type": "L2",  # Change as per your metric type
            "params": {"nprobe": 10}  # Adjust for performance
        }
        
        results = collection.search(query_vector, "title_vector", search_params, limit=5)
        
        logger.info(f"Search results for '{query_title}':")
        for result in results:
            logger.info(result)
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}")

