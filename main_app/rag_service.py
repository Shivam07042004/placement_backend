"""
RAG (Retrieval Augmented Generation) service using LangChain and OpenAI
"""
from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class JobMatch(BaseModel):
    """Job match result with reasoning"""
    job_id: int = Field(..., description="ID of the matched job")
    job_title: str = Field(..., description="Title of the job")
    company: str = Field(..., description="Company name")
    match_score: float = Field(..., description="Match score from 0 to 100")
    match_reasoning: str = Field(..., description="Why this job matches the resume")


class MatchedJobsResponse(BaseModel):
    """Response containing matched jobs"""
    matched_jobs: List[JobMatch] = Field(..., description="List of matched jobs")
    summary: str = Field(..., description="Overall summary of matches")


def process_resume_with_rag(
    resume_text: str,
    similar_jobs: List[tuple],
    api_key: str,
    base_url: str = "https://aipipe.org/openai/v1"
) -> MatchedJobsResponse:
    """
    Use RAG + LangChain with ChatOpenAI to process resume and find matches.
    
    Args:
        resume_text: Extracted resume text
        similar_jobs: List of (job, similarity_score) tuples from vector search
        api_key: OpenAI API key (or compatible service key)
        base_url: Base URL for the API endpoint (default: aipipe.org)
        
    Returns:
        MatchedJobsResponse: Structured response with matched jobs and reasoning
    """
    
    # Initialize LangChain components with custom base URL
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=api_key,
        base_url=base_url,
        temperature=0.3
    )
    
    # Format the similar jobs into context
    jobs_context = ""
    for job, similarity in similar_jobs:
        jobs_context += f"""
Job ID: {job.id}
Title: {job.title}
Company: {job.company}
Location: {job.location}
Salary: {job.salary}
Job Type: {job.jobtype}
Description: {job.description}
---"""
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_template("""
You are an expert recruiter and job matching AI. Analyze the provided resume and the candidate's top job matches.

CANDIDATE RESUME:
{resume}

POTENTIAL JOBS (retrieved from database based on semantic similarity):
{jobs}

Your task:
1. Analyze the candidate's skills, experience, and qualifications from the resume
2. For each job provided, determine if it's a good match
3. Provide a match score (0-100) for each job
4. Explain the reasoning for each match
5. Return the results as JSON

IMPORTANT: Return valid JSON only, no additional text. Use this structure:
{{
    "matched_jobs": [
        {{
            "job_id": <job_id>,
            "job_title": "<title>",
            "company": "<company>",
            "match_score": <0-100>,
            "match_reasoning": "<explanation of why this is a good match>"
        }}
    ],
    "summary": "<overall summary of the matches>"
}}

Only include jobs with match_score >= 50. Sort by match_score descending.
""")
    
    # Create chain with output parser
    parser = JsonOutputParser(pydantic_object=MatchedJobsResponse)
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "resume": resume_text,
            "jobs": jobs_context
        })
        
        # Ensure result is MatchedJobsResponse
        if isinstance(result, dict):
            result = MatchedJobsResponse(**result)
        
        # Filter jobs by score >= 50 and sort
        result.matched_jobs = [
            job for job in result.matched_jobs if job.match_score >= 50
        ]
        result.matched_jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        return result
        
    except Exception as e:
        raise ValueError(f"Error processing resume with RAG: {str(e)}")


def generate_resume_analysis(
    resume_text: str,
    api_key: str,
    base_url: str = "https://aipipe.org/openai/v1"
) -> Dict[str, any]:
    """
    Generate a quick analysis of the resume.
    
    Args:
        resume_text: Extracted resume text
        api_key: OpenAI API key (or compatible service key)
        base_url: Base URL for the API endpoint (default: aipipe.org)
        
    Returns:
        Dict: Analysis including key skills, experience level, etc.
    """
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=api_key,
        base_url=base_url,
        temperature=0.3
    )
    
    prompt = ChatPromptTemplate.from_template("""
Analyze this resume and provide insights:

RESUME:
{resume}

Provide analysis in JSON format:
{{
    "key_skills": ["skill1", "skill2", ...],
    "experience_level": "entry|mid|senior",
    "education": "description",
    "main_strengths": ["strength1", "strength2", ...],
    "job_preferences": "inferred preferences"
}}
""")
    
    parser = JsonOutputParser(pydantic_object=dict)
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({"resume": resume_text})
        return result
    except Exception as e:
        raise ValueError(f"Error analyzing resume: {str(e)}")
