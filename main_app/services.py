"""
Service utilities for resume parsing, embeddings, and job matching
"""
import os
import io
from typing import Optional, List, Tuple
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    
from PIL import Image
from pypdf import PdfReader
from docx import Document
from openai import OpenAI
import numpy as np
from django.db.models import F, Q


def extract_text_from_resume(file) -> str:
    """
    Extract text from uploaded resume file.
    Supports: PDF, DOCX, TXT, PNG, JPG, JPEG
    
    Args:
        file: Django uploaded file object
        
    Returns:
        str: Extracted text from the file
        
    Raises:
        ValueError: If file format is not supported
    """
    file_name = file.name.lower()
    file.seek(0)  # Reset file pointer
    
    try:
        if file_name.endswith('.pdf'):
            return _extract_from_pdf(file)
        elif file_name.endswith('.docx'):
            return _extract_from_docx(file)
        elif file_name.endswith('.txt'):
            return _extract_from_txt(file)
        elif file_name.endswith(('.png', '.jpg', '.jpeg')):
            return _extract_from_image(file)
        else:
            raise ValueError(f"Unsupported file format: {file_name}. Supported: PDF, DOCX, TXT, PNG, JPG")
    except Exception as e:
        raise ValueError(f"Error extracting text from {file_name}: {str(e)}")


def _extract_from_pdf(file) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def _extract_from_docx(file) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file.read()))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


def _extract_from_txt(file) -> str:
    """Extract text from TXT file"""
    try:
        return file.read().decode('utf-8').strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from TXT: {str(e)}")


def _extract_from_image(file) -> str:
    """Extract text from image using OCR (pytesseract)"""
    if not PYTESSERACT_AVAILABLE:
        raise ValueError(
            "Image OCR is not available. Please install Tesseract OCR: "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        )
    try:
        image = Image.open(io.BytesIO(file.read()))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from image: {str(e)}")


def get_embedding(text: str, api_key: str, base_url: str = "https://aipipe.org/openai/v1") -> List[float]:
    """
    Get embedding vector for text using OpenAI API or compatible service.
    
    Args:
        text: Text to embed
        api_key: OpenAI API key (or compatible service key)
        base_url: Base URL for the API endpoint (default: aipipe.org)
        
    Returns:
        List[float]: Embedding vector (1536 dimensions)
    """
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        float: Similarity score between 0 and 1
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def find_similar_jobs(resume_embedding: List[float], top_k: Optional[int] = None, min_similarity: float = 0.0) -> List[Tuple]:
    """
    Find most similar jobs to resume using database embeddings.
    Uses cosine similarity without vector database.
    
    Args:
        resume_embedding: Embedding vector of the resume
        top_k: Optional number of top similar jobs to return. If None, returns all jobs above the similarity threshold.
        min_similarity: Minimum cosine similarity threshold for returned jobs.
        
    Returns:
        List[Tuple]: List of (job, similarity_score) tuples, sorted by similarity
    """
    from main_app.models import JobEmbedding
    
    # Get all job embeddings
    job_embeddings = JobEmbedding.objects.select_related('job').all()
    
    similarities = []
    for job_emb in job_embeddings:
        similarity = cosine_similarity(resume_embedding, job_emb.embedding)
        if similarity >= min_similarity:
            similarities.append((job_emb.job, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    if top_k is not None:
        return similarities[:top_k]
    return similarities[:top_k]


def create_job_summary(job) -> str:
    """
    Create a summary text of job for embedding.
    
    Args:
        job: Job model instance
        
    Returns:
        str: Combined job text
    """
    summary = f"""
    Job Title: {job.title}
    Company: {job.company}
    Job Type: {job.jobtype}
    Type: {job.type}
    Location: {job.location}
    Salary: {job.salary}
    Description: {job.description}
    """
    return summary.strip()
