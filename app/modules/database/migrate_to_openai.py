#!/usr/bin/env python3
"""
Migration script to transfer documents from local ChromaDB to OpenAI Vector Stores

This script:
1. Extracts documents from local ChromaDB
2. Uploads them to OpenAI Vector Stores  
3. Verifies the migration was successful
4. Optionally backs up local data
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.modules.database.vector_store import VectorStore
from app.modules.database.openai_vector_store import OpenAIVectorStore


def extract_documents_from_local() -> List[Dict[str, Any]]:
    """Extract all documents from local ChromaDB"""
    try:
        print("📂 Connecting to local ChromaDB...")
        local_store = VectorStore(
            collection_name="job_description_docs",
            embedding_function="sentence_transformers"
        )
        
        # Get collection info
        info = local_store.get_collection_info()
        print(f"📊 Found {info.get('count', 0)} documents in local store")
        
        # Get all documents
        collection = local_store.collection
        results = collection.get()
        
        documents = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                doc_id = results['ids'][i] if results['ids'] else f"doc_{i}"
                
                documents.append({
                    'id': doc_id,
                    'content': doc,
                    'metadata': metadata
                })
        
        print(f"✅ Extracted {len(documents)} documents")
        return documents
        
    except Exception as e:
        print(f"❌ Error extracting from local store: {e}")
        return []


def upload_documents_to_openai(documents: List[Dict[str, Any]]) -> bool:
    """Upload documents to OpenAI Vector Store"""
    try:
        print("☁️ Connecting to OpenAI Vector Store...")
        openai_store = OpenAIVectorStore(vector_store_name="job_description_docs")
        
        if not documents:
            print("⚠️ No documents to upload")
            return False
        
        # Prepare documents for upload
        doc_texts = [doc['content'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        print(f"📤 Uploading {len(doc_texts)} documents to OpenAI...")
        
        # Upload documents
        file_ids = openai_store.add_documents(
            documents=doc_texts,
            metadatas=metadatas
        )
        
        print(f"✅ Successfully uploaded {len(file_ids)} documents")
        print(f"🆔 File IDs: {file_ids}")
        
        # Wait a moment for processing
        print("⏳ Waiting for OpenAI processing...")
        time.sleep(5)
        
        # Verify upload
        store_info = openai_store.get_vector_store_info()
        print(f"📊 OpenAI Vector Store Info:")
        print(f"   Name: {store_info.get('name', 'N/A')}")
        print(f"   File Count: {store_info.get('file_count', 0)}")
        print(f"   Status: {store_info.get('status', 'N/A')}")
        print(f"   Usage: {store_info.get('usage_bytes', 0)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to OpenAI: {e}")
        return False


def test_openai_search() -> bool:
    """Test search functionality on OpenAI Vector Store"""
    try:
        print("🔍 Testing OpenAI Vector Store search...")
        openai_store = OpenAIVectorStore(vector_store_name="job_description_docs")
        
        test_queries = [
            "What programming languages are required?",
            "What are the main responsibilities?",
            "What experience is needed?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = openai_store.similarity_search(query, n_results=1)
            
            if results:
                print(f"✅ Found {len(results)} results")
                for result in results:
                    print(f"📝 Preview: {result.get('document', '')[:100]}...")
            else:
                print("⚠️ No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False


def backup_local_data(documents: List[Dict[str, Any]]) -> bool:
    """Create a backup of local data"""
    try:
        backup_file = project_root / "data" / "local_chromadb_backup.json"
        backup_file.parent.mkdir(exist_ok=True)
        
        print(f"💾 Creating backup at {backup_file}")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'documents': documents,
                'source': 'local_chromadb',
                'migration_version': '1.0'
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup created: {backup_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False


def main():
    """Main migration function"""
    print("🚀 STARTING MIGRATION: Local ChromaDB → OpenAI Vector Stores")
    print("=" * 60)
    
    # Step 1: Extract documents from local store
    documents = extract_documents_from_local()
    if not documents:
        print("❌ No documents found to migrate")
        return
    
    # Step 2: Create backup
    backup_success = backup_local_data(documents)
    if not backup_success:
        print("⚠️ Warning: Backup failed, but continuing...")
    
    # Step 3: Upload to OpenAI
    upload_success = upload_documents_to_openai(documents)
    if not upload_success:
        print("❌ Migration failed during upload")
        return
    
    # Step 4: Test the new setup
    test_success = test_openai_search()
    if not test_success:
        print("⚠️ Warning: Search testing failed")
    
    print("\n🎉 MIGRATION COMPLETE!")
    print("=" * 60)
    print("✅ Your documents are now stored in OpenAI Vector Stores")
    print("💡 Next steps:")
    print("   1. Update Info Advisor to use OpenAI Vector Store")
    print("   2. Test the complete system")
    print("   3. Optional: Clean up local ChromaDB if satisfied")
    

if __name__ == "__main__":
    main() 