import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from app.tools.rag.vector_store import vector_store

logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation for knowledge queries"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.initialized = False
    
    async def initialize(self):
        """Initialize RAG with policy documents"""
        if not self.initialized:
            # Add sample policy documents
            documents = [
                {
                    "content": "Personal loan eligibility: Applicants must be between 21-60 years old with minimum monthly income of ₹25,000. Credit score should be above 650.",
                    "metadata": {"category": "eligibility"}
                },
                {
                    "content": "Interest rates range from 10.5% to 18% per annum depending on credit profile and loan amount.",
                    "metadata": {"category": "interest_rates"}
                },
                {
                    "content": "Required documents include: salary slips (last 3 months), PAN card, Aadhaar card, and bank statements (last 6 months).",
                    "metadata": {"category": "documents"}
                },
                {
                    "content": "Loan amount ranges from ₹50,000 to ₹50,00,000. Repayment tenure options: 12 to 60 months.",
                    "metadata": {"category": "loan_details"}
                },
                {
                    "content": "Processing time is typically 2-3 business days after document verification. Instant approvals available for pre-qualified customers.",
                    "metadata": {"category": "processing"}
                }
            ]
            
            for doc in documents:
                await vector_store.add_document(doc["content"], doc["metadata"])
            
            self.initialized = True
            logger.info("RAG engine initialized with policy documents")
    
    async def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Query knowledge base and generate answer
        
        Args:
            question: User's question
            top_k: Number of relevant documents to retrieve
            
        Returns:
            {
                "answer": str,
                "sources": list,
                "confidence": float
            }
        """
        if not self.initialized:
            await self.initialize()
        
        # Retrieve relevant documents
        results = await vector_store.search(question, top_k=top_k)
        
        if not results:
            return {
                "answer": "I don't have specific information about that. Please contact our support team for detailed assistance.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Construct answer from retrieved documents
        context = "\n\n".join([r["content"] for r in results])
        
        # For MVP, we use simple retrieval without generation
        # In production, you'd pass context to LLM for answer generation
        answer = results[0]["content"]
        
        return {
            "answer": answer,
            "sources": [r["metadata"] for r in results],
            "confidence": results[0]["score"]
        }


rag_engine = RAGEngine()
