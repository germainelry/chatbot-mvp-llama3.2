"""
RAG service for vector embeddings and semantic search.
Uses sentence-transformers for embeddings and ChromaDB for vector storage.
"""
import os
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

# Try to import sentence-transformers, fallback if not available
EMBEDDING_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    print("⚠️  sentence-transformers or chromadb not available, using fallback")

# Initialize embedding model (lazy loading)
_embedding_model = None
_chroma_client = None
_chroma_collection = None

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def get_embedding_model():
    """Lazy load the embedding model."""
    global _embedding_model
    if not EMBEDDING_AVAILABLE:
        return None
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_chroma_collection():
    """Initialize and return ChromaDB collection."""
    global _chroma_client, _chroma_collection
    if not EMBEDDING_AVAILABLE:
        return None
    
    if _chroma_client is None:
        # Use persistent storage in backend directory
        chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))
    
    if _chroma_collection is None:
        # Get or create collection
        try:
            _chroma_collection = _chroma_client.get_collection("knowledge_base")
        except:
            _chroma_collection = _chroma_client.create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
    
    return _chroma_collection


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate vector embedding for text.
    Returns None if embeddings are not available.
    """
    if not EMBEDDING_AVAILABLE:
        return None
    
    model = get_embedding_model()
    if model is None:
        return None
    
    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def search_knowledge_base_vector(query: str, db: Session, top_k: int = 3) -> List[Dict]:
    """
    Search knowledge base using vector similarity.
    Falls back to keyword search if embeddings are not available.
    """
    if not EMBEDDING_AVAILABLE:
        # Fallback to keyword search
        return search_knowledge_base_keyword(query, db, top_k)
    
    collection = get_chroma_collection()
    if collection is None:
        return search_knowledge_base_keyword(query, db, top_k)
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        return search_knowledge_base_keyword(query, db, top_k)
    
    try:
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Map results to article format
        matched_articles = []
        if results['ids'] and len(results['ids'][0]) > 0:
            from app.models import KnowledgeBase
            for i, article_id in enumerate(results['ids'][0]):
                # Get article from database
                article = db.query(KnowledgeBase).filter_by(id=int(article_id)).first()
                
                if article:
                    distance = results['distances'][0][i] if 'distances' in results else 0.0
                    similarity = 1.0 - distance  # Convert distance to similarity
                    
                    matched_articles.append({
                        "id": article.id,
                        "title": article.title,
                        "content": article.content,
                        "category": article.category,
                        "match_score": similarity,
                        "similarity": similarity
                    })
        
        # If no results from ChromaDB, fallback to keyword search
        if not matched_articles:
            return search_knowledge_base_keyword(query, db, top_k)
        
        return matched_articles
    
    except Exception as e:
        print(f"Error in vector search: {e}")
        return search_knowledge_base_keyword(query, db, top_k)


def search_knowledge_base_keyword(query: str, db: Session, top_k: int = 3) -> List[Dict]:
    """Fallback keyword-based search."""
    from app.models import KnowledgeBase
    
    query_lower = query.lower()
    all_articles = db.query(KnowledgeBase).all()
    
    matched_articles = []
    for article in all_articles:
        article_text = f"{article.title} {article.content} {article.tags}".lower()
        query_words = set(query_lower.split())
        article_words = set(article_text.split())
        common_words = query_words.intersection(article_words)
        
        if common_words:
            match_score = len(common_words) / len(query_words) if query_words else 0
            matched_articles.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "category": article.category,
                "match_score": match_score,
                "similarity": match_score
            })
    
    matched_articles.sort(key=lambda x: x["match_score"], reverse=True)
    return matched_articles[:top_k]


def add_article_to_vector_db(article_id: int, title: str, content: str, db: Session):
    """
    Add or update article in vector database.
    """
    if not EMBEDDING_AVAILABLE:
        return
    
    collection = get_chroma_collection()
    if collection is None:
        return
    
    # Generate embedding for article
    article_text = f"{title} {content}"
    embedding = generate_embedding(article_text)
    
    if embedding is None:
        return
    
    try:
        # Add to ChromaDB
        collection.upsert(
            ids=[str(article_id)],
            embeddings=[embedding],
            documents=[article_text],
            metadatas=[{"article_id": article_id, "title": title}]
        )
        
        # Also update embedding in SQLite
        from app.models import KnowledgeBase
        article = db.query(KnowledgeBase).filter_by(id=article_id).first()
        if article:
            article.embedding = embedding
            db.commit()
    except Exception as e:
        print(f"Error adding article to vector DB: {e}")


def initialize_vector_db(db: Session):
    """
    Initialize vector database with existing knowledge base articles.
    """
    if not EMBEDDING_AVAILABLE:
        return
    
    from app.models import KnowledgeBase
    
    articles = db.query(KnowledgeBase).all()
    collection = get_chroma_collection()
    
    if collection is None:
        return
    
    try:
        # Clear existing collection
        try:
            _chroma_client.delete_collection("knowledge_base")
        except:
            pass
        
        _chroma_collection = _chroma_client.create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add all articles
        for article in articles:
            add_article_to_vector_db(article.id, article.title, article.content, db)
        
        print(f"✅ Initialized vector DB with {len(articles)} articles")
    except Exception as e:
        print(f"Error initializing vector DB: {e}")

