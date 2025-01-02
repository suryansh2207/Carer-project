#!/bin/bash

# run.sh - Script to run all components of the article crawler and search system

# Check Python version
python_version=$(python -c 'import sys; print(sys.version_info[0:2])')
if [[ $python_version != "(3, 12)" ]]; then
    echo "This script requires Python 3.12"
    exit 1
fi

# # Check if virtual environment exists, if not create it
# if [ ! -d "venv" ]; then
#     echo "Creating virtual environment..."
#     python -m venv venv
# fi

# # Activate virtual environment
# # source venv/bin/activate  # For Unix/Linux
# # Or use: 
#  .\venv\Scripts\activate  # For Windows

# Install required packages
# echo "Installing required packages..."
# pip install --upgrade pip
# pip install requests beautifulsoup4 mysql-connector-python \
#     transformers torch sentence-transformers keybert pymilvus \
#     configparser numpy typing_extensions

# Run database setup
echo "Setting up database..."
mysql -u root -p < carer-sql.sql

# Run components in sequence
echo "Starting crawler..."
python -c "from crawler import fetch_articles; fetch_articles()"

echo "Running summarization and keyword extraction..."
python -c "from summarizer import process_all_articles; process_all_articles()"

echo "Starting required services..."
if [[ "$OSTYPE" == "msys" ]]; then
    ./start_services.bat
else
    ./start_services.sh
fi

echo "Setting up vector store..."
python -c "from vector_store import init_vector_store, process_articles; init_vector_store(); process_articles()"

echo "Starting query interface..."
python -c "from query import search_articles; print('Query interface ready.')"

# # Deactivate virtual environment
# deactivate

echo "All components have been executed successfully!"