from django.db import models

def get_default_batch():
    return []

# Create your models here.
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title=models.TextField()
    company=models.TextField()
    jobtype=models.TextField()
    type=models.TextField()
    imgurl=models.TextField()
    salary=models.TextField(default="N/A")
    batch=models.JSONField(default=get_default_batch)
    link=models.TextField()
    location=models.TextField(default="N/A")
    locationurl=models.TextField(default="N/A")
    admin=models.TextField(null=False,default="admin")
    description=models.TextField(default="N/A")

    def __str__(self):
        return self.title


class JobEmbedding(models.Model):
    """
    Stores vector embeddings for jobs.
    Used for semantic search when matching resumes to jobs.
    """
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='embedding')
    embedding = models.JSONField()  # Stores list of floats (1536 dimensions for OpenAI)
    job_text = models.TextField()  # Combined text from title, company, description for chunking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['job']),
        ]

    def __str__(self):
        return f"Embedding for {self.job.title}"
