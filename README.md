# Langchain Outline Document Loader

## Overview

`langchain-outline` provides a `DocumentLoader` for Langchain that allows you to load documents directly from an [Outline](https://www.getoutline.com/) knowledge base instance.

This loader uses the Outline API to fetch all documents within your instance.

## Installation

```bash
pip install langchain-outline
```

## Configuration

The loader requires the URL of your Outline instance and an API key for authentication. 

## Usage

````python
import os
from langchain_outline.outline import OutlineLoader

# Option 1: Using environment variables (ensure they are set)
# os.environ["OUTLINE_INSTANCE_URL"] = "YOUR_OUTLINE_URL"
# os.environ["OUTLINE_API_KEY"] = "YOUR_API_KEY"
# loader = OutlineLoader()

# Option 2: Passing parameters directly
loader = OutlineLoader(
    outline_base_url="YOUR_OUTLINE_URL",
    outline_api_key="YOUR_API_KEY"
)

# Load documents (iteratively)
docs_iterator = loader.lazy_load()
for doc in docs_iterator:
    print(f"Loaded document: {doc.metadata['title']}")
    # Process the document...

# Or load all documents into a list (might consume more memory for large instances)
# all_docs = loader.load()
# print(f"Loaded {len(all_docs)} documents.")
```
Replace "YOUR_OUTLINE_URL" and "YOUR_API_KEY" with your actual Outline instance URL and API key.
