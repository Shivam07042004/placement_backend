from django.core.management.base import BaseCommand
from main_app.models import Job


class Command(BaseCommand):
    help = 'Create sample job data for testing'

    def handle(self, *args, **options):
        # Clear existing jobs
        Job.objects.all().delete()
        
        # Create sample jobs
        jobs_data = [
            {
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Francisco, CA',
                'description': 'We are looking for a skilled software engineer to join our team.',
                'requirements': 'Bachelor\'s degree in Computer Science, Python, Django experience',
                'salary': 90000,
                'job_type': 'Full-time'
            },
            {
                'title': 'Frontend Developer',
                'company': 'Web Solutions',
                'location': 'New York, NY', 
                'description': 'Join our frontend team to build amazing user interfaces.',
                'requirements': 'React, JavaScript, HTML, CSS experience required',
                'salary': 75000,
                'job_type': 'Full-time'
            },
            {
                'title': 'Data Scientist',
                'company': 'Data Insights',
                'location': 'Remote',
                'description': 'Analyze data and build machine learning models.',
                'requirements': 'Python, Machine Learning, Statistics background',
                'salary': 95000,
                'job_type': 'Contract'
            }
        ]
        
        for job_data in jobs_data:
            job = Job.objects.create(**job_data)
            self.stdout.write(
                self.style.SUCCESS(f'Created job: {job.title} at {job.company}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(jobs_data)} sample jobs')
        )