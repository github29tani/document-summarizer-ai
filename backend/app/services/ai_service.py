from groq import Groq
from typing import Dict, List, Optional
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import settings

class AIService:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Keep for token counting
        
        # Initialize embedding model for semantic search
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    async def generate_summary(
        self, 
        text: str, 
        document_name: str,
        max_summary_length: int = 500
    ) -> Dict[str, any]:
        """Generate AI summary of document text"""
        
        # Count tokens in input text
        token_count = self.count_tokens(text)
        
        try:
            if token_count <= 3000:
                # Short document - direct summarization
                summary_result = await self._summarize_short_text(text, document_name, max_summary_length)
            else:
                # Long document - chunk and summarize
                summary_result = await self._summarize_long_text(text, document_name, max_summary_length)
            
            # Extract key points
            key_points = await self._extract_key_points(text, summary_result["summary"])
            summary_result["key_points"] = key_points
            
            return summary_result
            
        except Exception as e:
            raise Exception(f"AI summarization failed: {str(e)}")

    async def _summarize_short_text(
        self, 
        text: str, 
        document_name: str, 
        max_length: int
    ) -> Dict[str, any]:
        """Summarize short text directly"""
        
        prompt = f"""
        Please provide a comprehensive summary of the following document titled "{document_name}".
        
        Requirements:
        - Maximum {max_length} words
        - Focus on main ideas and key information
        - Use clear, professional language
        - Maintain the document's tone and context
        
        Document text:
        {text}
        
        Summary:
        """
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert document summarizer. Provide clear, concise, and comprehensive summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_length * 2,  # Allow some buffer
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        return {
            "summary": summary,
            "model": "llama-3.3-70b-versatile",
            "method": "direct"
        }

    async def _summarize_long_text(
        self, 
        text: str, 
        document_name: str, 
        max_length: int
    ) -> Dict[str, any]:
        """Summarize long text using chunking strategy"""
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"""
            Summarize this section (part {i+1} of {len(chunks)}) of the document "{document_name}":
            
            {chunk}
            
            Provide a concise summary focusing on the main points:
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing document sections. Focus on key information and main ideas."},
                    {"role": "user", "content": chunk_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            chunk_summaries.append(response.choices[0].message.content.strip())
        
        # Combine chunk summaries into final summary
        combined_summaries = "\n\n".join(chunk_summaries)
        
        final_prompt = f"""
        Based on the following section summaries from the document "{document_name}", 
        create a comprehensive final summary of maximum {max_length} words:
        
        Section Summaries:
        {combined_summaries}
        
        Final Summary:
        """
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at creating comprehensive summaries from multiple sections. Ensure coherence and completeness."},
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=max_length * 2,
            temperature=0.3
        )
        
        final_summary = response.choices[0].message.content.strip()
        
        return {
            "summary": final_summary,
            "model": "llama-3.3-70b-versatile",
            "method": "chunked",
            "chunks_processed": len(chunks)
        }

    async def _extract_key_points(self, original_text: str, summary: str) -> List[str]:
        """Extract key points from the document"""
        
        prompt = f"""
        Based on the following document summary, extract 5-8 key points that capture the most important information:
        
        Summary:
        {summary}
        
        Please provide key points as a numbered list, with each point being a concise statement (1-2 sentences max).
        Focus on actionable insights, main conclusions, and critical information.
        
        Key Points:
        """
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at extracting key points from document summaries. Focus on the most important and actionable information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.2
        )
        
        key_points_text = response.choices[0].message.content.strip()
        
        # Parse the numbered list into individual points
        key_points = []
        lines = key_points_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering/bullets and clean up
                point = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if point:
                    key_points.append(point)
        
        return key_points[:8]  # Limit to 8 points

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks using SentenceTransformers"""
        
        try:
            # Generate embeddings using local model
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
            
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")

    async def semantic_search(
        self, 
        query: str, 
        document_embeddings: List[Dict], 
        top_k: int = 5
    ) -> List[Dict]:
        """Perform semantic search using embeddings"""
        
        # Generate query embedding
        query_embedding = await self.generate_embeddings([query])
        query_vector = query_embedding[0]
        
        # Calculate similarity scores (cosine similarity)
        results = []
        for doc_embedding in document_embeddings:
            similarity = self._cosine_similarity(query_vector, doc_embedding["embedding"])
            results.append({
                **doc_embedding,
                "similarity_score": similarity
            })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)

    async def extract_highlights(
        self, 
        text: str, 
        summary: str
    ) -> List[Dict[str, any]]:
        """Extract important text highlights from document"""
        
        prompt = f"""
        Based on the document text and its summary, identify 5-10 important text passages that should be highlighted.
        Focus on:
        - Key definitions or concepts
        - Important conclusions or findings
        - Critical data or statistics
        - Main arguments or points
        
        Document Summary:
        {summary}
        
        Document Text (first 2000 characters):
        {text[:2000]}
        
        Please identify important passages and classify them as:
        - "key-point": Main arguments or conclusions
        - "important": Critical information or data
        - "definition": Key terms or concepts
        
        Format your response as a JSON array with objects containing:
        - "text": the exact text passage
        - "type": classification (key-point, important, or definition)
        - "confidence": confidence score (0.0-1.0)
        """
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at identifying important passages in documents. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        try:
            import json
            highlights = json.loads(response.choices[0].message.content.strip())
            return highlights if isinstance(highlights, list) else []
        except json.JSONDecodeError:
            # Fallback: return empty list if JSON parsing fails
            return []
