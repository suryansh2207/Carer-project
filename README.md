# Carer Project

This project is designed to crawl, process, and query oncology-related articles from the web. It includes components for web scraping, data storage, summarization, keyword extraction, and vector-based search.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Components](#components)
- [Configuration](#configuration)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/suryansh2207/Carer-project.git
    cd carer-project
    ```
    
## Usage

To run the entire pipeline, execute the run_all.sh script:
```bash
./run_all.sh
```

## This script will:

1. Start the necessary services.
2. Set up the vector store.
3. Process and store articles.
4. Run a query interface for searching articles.

## Components

Crawler
- The crawler.py script is responsible for crawling oncology-related articles from the web and storing them in the MySQL database.

Summarizer
- The summarizer.py script processes articles to generate summaries and extract keywords using pre-trained models.

Query
- The query.py script provides functionality to search articles based on query text, including vector-based similarity search.

Vector Store
- The vector_store.py script initializes the vector store and processes articles for vector-based search.

##Configuration

The config.in file contains configuration settings for the project, including database connection details and Milvus settings.

