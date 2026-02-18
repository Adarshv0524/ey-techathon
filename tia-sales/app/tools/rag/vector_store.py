import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """Simple in-memory vector store for document retrieval"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[np.ndarray] = []
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None):
        """Add document to vector store"""
        embedding = self.embedding_model.encode(content)
        
        self.documents.append({
            "content": content,
            "metadata": metadata or {}
        })
        self.embeddings.append(embedding)
        
        logger.info(f"Added document to vector store: {content[:50]}...")
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if not self.documents:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate cosine similarity
        similarities = []
        for doc_embedding in self.embeddings:
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append(similarity)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "content": self.documents[idx]["content"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(similarities[idx])
            })
        
        return results
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


vector_store = VectorStore()
