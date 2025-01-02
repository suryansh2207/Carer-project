from transformers import pipeline
from keybert import KeyBERT
import torch
from typing import Tuple, List
import logging

from crawler import connect_db

logger = logging.getLogger(__name__)

def init_models():
    """Initialize the summarization and keyword extraction models"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    summarizer = pipeline("summarization", 
                         model="facebook/bart-large-cnn",
                         device=device)
    keyword_model = KeyBERT()
    return summarizer, keyword_model

def process_article(text: str, summarizer, keyword_model) -> Tuple[str, List[str]]:
    """Generate summary and keywords for an article"""
    try:
        summary = summarizer(text, max_length=130, min_length=30)[0]['summary_text']
        keywords = [kw[0] for kw in keyword_model.extract_keywords(text, top_n=5)]
        return summary, keywords
    except Exception as e:
        logger.error(f"Error processing article: {str(e)}")
        return "", []

def update_article_analysis(db_conn, article_id: int, summary: str, keywords: List[str]):
    """Update article with summary and keywords"""
    cursor = db_conn.cursor()
    try:
        query = """
        UPDATE articles 
        SET summary = %s, keywords = %s
        WHERE id = %s
        """
        cursor.execute(query, (summary, ','.join(keywords), article_id))
        db_conn.commit()
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {str(e)}")
        db_conn.rollback()
    finally:
        cursor.close()

def process_all_articles():
    """Process all unprocessed articles"""
    db_conn = connect_db()
    summarizer, keyword_model = init_models()
    
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("SELECT id, abstract FROM articles WHERE summary IS NULL")
        articles = cursor.fetchall()
        
        for article in articles:
            summary, keywords = process_article(article['abstract'], summarizer, keyword_model)
            if summary and keywords:
                update_article_analysis(db_conn, article['id'], summary, keywords)
    finally:
        cursor.close()
        db_conn.close()