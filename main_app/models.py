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
