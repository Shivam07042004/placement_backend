"""
Management command to create embeddings for all jobs.
Usage: python manage.py embed_jobs --api-key YOUR_OPENAI_API_KEY
"""
from django.core.management.base import BaseCommand
from main_app.models import Job, JobEmbedding
from main_app.services import get_embedding, create_job_summary


class Command(BaseCommand):
    help = 'Create embeddings for all jobs using OpenAI API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            required=True,
            help='OpenAI API key for creating embeddings'
        )
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Recreate embeddings even if they already exist'
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        recreate = options['recreate']

        if not api_key or len(api_key) < 10:
            self.stdout.write(self.style.ERROR('Invalid OpenAI API key'))
            return

        self.stdout.write('Starting job embedding process...')

        jobs = Job.objects.all()
        total_jobs = jobs.count()

        if total_jobs == 0:
            self.stdout.write(self.style.WARNING('No jobs found in database'))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        for idx, job in enumerate(jobs, 1):
            try:
                # Check if embedding already exists
                try:
                    job_embedding = JobEmbedding.objects.get(job=job)
                    if not recreate:
                        skipped_count += 1
                        self.stdout.write(
                            f'[{idx}/{total_jobs}] Skipping {job.title} (embedding exists)'
                        )
                        continue
                except JobEmbedding.DoesNotExist:
                    job_embedding = None

                # Create job summary
                job_summary = create_job_summary(job)

                # Get embedding from OpenAI
                self.stdout.write(f'[{idx}/{total_jobs}] Embedding: {job.title}...')
                embedding = get_embedding(job_summary, api_key, base_url="https://aipipe.org/openai/v1")

                # Create or update embedding record
                if job_embedding is None:
                    JobEmbedding.objects.create(
                        job=job,
                        embedding=embedding,
                        job_text=job_summary
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  [OK] Created embedding'))
                else:
                    job_embedding.embedding = embedding
                    job_embedding.job_text = job_summary
                    job_embedding.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  [OK] Updated embedding'))

            except Exception as e:
                error_count += 1
                error_msg = f'Job {job.id} ({job.title}): {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f'  [FAIL] Error: {error_msg}'))

        # Print summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Embedding Process Complete!'))
        self.stdout.write('='*50)
        self.stdout.write(f'Total jobs: {total_jobs}')
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

        if errors:
            self.stdout.write('\nErrors encountered:')
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
