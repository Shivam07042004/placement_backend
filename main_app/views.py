from django.shortcuts import render
from .models import Job, JobEmbedding
from .serializers import JobSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from django.db import connection, transaction
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from .services import (
    extract_text_from_resume, 
    get_embedding, 
    find_similar_jobs,
    create_job_summary
)
from .rag_service import process_resume_with_rag


def _format_job_link(link):
    """
    Ensure job link has a protocol (https://).
    If link doesn't start with http:// or https://, prepend https://
    """
    if not link:
        return link
    
    link = link.strip()
    if link.startswith(('http://', 'https://')):
        return link
    
    return f"https://{link}"


# Create your views here.
def api_root(request):
    return JsonResponse({
        "message": "Welcome to Placement API",
        "version": "1.0",
        "endpoints": {
            "jobs": "/api/jobs/",
            "job_detail": "/api/jobs/{id}/",
            "login": "/api/login/",
            "debug": "/api/debug/",
            "admin": "/admin/"
        }
    })

def debug_info(request):
    """Debug endpoint to check database connection and data"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_connected = True
    except Exception as e:
        db_connected = False
        db_error = str(e)
    
    try:
        # Get job count
        job_count = Job.objects.count()
        jobs_exist = True
    except Exception as e:
        job_count = 0
        jobs_exist = False
        jobs_error = str(e)
    
    debug_data = {
        "database": {
            "connected": db_connected,
            "error": db_error if not db_connected else None,
            "engine": settings.DATABASES['default']['ENGINE'],
            "host": settings.DATABASES['default'].get('HOST'),
            "name": settings.DATABASES['default'].get('NAME'),
        },
        "jobs": {
            "count": job_count,
            "exist": jobs_exist,
            "error": jobs_error if not jobs_exist else None,
        },
        "environment": {
            "debug": settings.DEBUG,
            "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
        }
    }
    
    return JsonResponse(debug_data)
class JobList(APIView):

    def get(self,request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        payload = request.data.copy()
        request_api_key = payload.pop('openai_api_key', '')
        if isinstance(request_api_key, list):
            request_api_key = request_api_key[0] if request_api_key else ''

        serializer = JobSerializer(data=payload)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    job = serializer.save()

                    # Try to create embedding if API key is available
                    api_key = str(request_api_key).strip()
                    if not api_key:
                        api_key = getattr(settings, 'OPENAI_API_KEY', '').strip()

                    # Only create embedding if API key is provided
                    if api_key and len(api_key) > 10:
                        try:
                            job_summary = create_job_summary(job)
                            embedding = get_embedding(
                                job_summary,
                                api_key,
                                base_url=getattr(settings, 'OPENAI_BASE_URL', "https://aipipe.org/openai/v1")
                            )

                            JobEmbedding.objects.update_or_create(
                                job=job,
                                defaults={
                                    'embedding': embedding,
                                    'job_text': job_summary
                                }
                            )
                        except Exception as e:
                            # Log embedding error but don't fail job creation
                            print(f"Warning: Failed to create job embedding: {str(e)}")
                    else:
                        print("Info: Skipping embedding creation - no OpenAI API key provided")

                return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": f"Failed to create job: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class JobDetail(APIView):

    def get_object(self,pk):
        try:
            job = Job.objects.get(pk=pk)
            return job
        except Job.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get(self,request,pk):
        job = self.get_object(pk)
        serializer = JobSerializer(job)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def put(self,request,pk):
        job = self.get_object(pk)
        serializer = JobSerializer(job,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status = status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,pk):
        job = self.get_object(pk)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginAPI(APIView):
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user_obj = authenticate(username=username, password=password)

        if user_obj:
            token, created = Token.objects.get_or_create(user=user_obj)
            return Response({"message": "Login successful", "token": token.key}, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class ResumeMatchJobsAPI(APIView):
    """
    API endpoint to upload resume and match with jobs.
    Uses user's OpenAI API key for embeddings and matching.
    """
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        """
        Upload resume and get matched jobs.
        
        Request:
            - resume: file (PDF, DOCX, TXT, PNG, JPG)
            - openai_api_key: string
            
        Response:
            - matched_jobs: list of jobs with scores
            - summary: overall matching summary
        """
        try:
            # Validate required fields
            if 'resume' not in request.FILES:
                return Response(
                    {"error": "Resume file is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if 'openai_api_key' not in request.data:
                return Response(
                    {"error": "OpenAI API key is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            resume_file = request.FILES['resume']
            api_key = request.data['openai_api_key'].strip()
            
            # Validate API key format
            if not api_key or len(api_key) < 10:
                return Response(
                    {"error": "Invalid OpenAI API key format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract text from resume
            try:
                resume_text = extract_text_from_resume(resume_file)
                if not resume_text or len(resume_text) < 10:
                    return Response(
                        {"error": "Could not extract enough text from resume. Please check the file."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if job embeddings exist
            embedding_count = JobEmbedding.objects.count()
            if embedding_count == 0:
                return Response(
                    {"error": "Job embeddings not yet created. Please contact admin to initialize embeddings."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Get resume embedding
            try:
                resume_embedding = get_embedding(resume_text, api_key, base_url="https://aipipe.org/openai/v1")
            except Exception as e:
                if "401" in str(e) or "invalid" in str(e).lower():
                    return Response(
                        {"error": "Invalid OpenAI API key. Please check your key and try again."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                return Response(
                    {"error": f"Error getting embedding: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Find similar jobs using vector search, only keeping jobs with >= 50% cosine similarity
            similar_jobs = find_similar_jobs(resume_embedding, min_similarity=0.5)
            
            if not similar_jobs:
                return Response(
                    {"error": "No matching jobs found with at least 50% similarity"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Process with RAG to get final matches with reasoning
            try:
                matched_jobs_response = process_resume_with_rag(
                    resume_text,
                    similar_jobs,
                    api_key,
                    base_url="https://aipipe.org/openai/v1"
                )
            except Exception as e:
                return Response(
                    {"error": f"Error processing resume: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Serialize response
            response_data = {
                "matched_jobs": [
                    {
                        "job_id": job.job_id,
                        "job_title": match.job_title,
                        "company": match.company,
                        "match_score": match.match_score,
                        "match_reasoning": match.match_reasoning,
                        "salary": job.job.salary,
                        "location": job.job.location,
                        "job_type": job.job.jobtype,
                        "link": f"/jobs/{job.job_id}"
                    }
                    for match in matched_jobs_response.matched_jobs
                    for job in [
                        JobEmbedding.objects.get(job_id=match.job_id)
                    ]
                ],
                "summary": matched_jobs_response.summary,
                "total_matches": len(matched_jobs_response.matched_jobs)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmbedAllJobsAPI(APIView):
    """
    Management endpoint to create embeddings for all jobs.
    Should be called after adding new jobs or during initialization.
    """
    
    def post(self, request):
        """
        Create embeddings for all jobs that don't have embeddings yet.
        
        Request:
            - openai_api_key: string
            
        Response:
            - created_count: number of new embeddings created
            - updated_count: number of embeddings updated
        """
        try:
            if 'openai_api_key' not in request.data:
                return Response(
                    {"error": "OpenAI API key is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            api_key = request.data['openai_api_key'].strip()
            
            if not api_key or len(api_key) < 10:
                return Response(
                    {"error": "Invalid OpenAI API key format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all jobs
            jobs = Job.objects.all()
            created_count = 0
            updated_count = 0
            errors = []
            
            from .services import create_job_summary
            
            for job in jobs:
                try:
                    # Create job summary
                    job_summary = create_job_summary(job)
                    
                    # Get embedding
                    embedding = get_embedding(job_summary, api_key, base_url="https://aipipe.org/openai/v1")
                    
                    # Create or update embedding record
                    job_embedding, created = JobEmbedding.objects.update_or_create(
                        job=job,
                        defaults={
                            'embedding': embedding,
                            'job_text': job_summary
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(f"Error embedding job {job.id}: {str(e)}")
            
            response_data = {
                "message": "Embedding process completed",
                "created_count": created_count,
                "updated_count": updated_count,
                "total_jobs": jobs.count(),
                "errors": errors if errors else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
