# placement_backend

Django REST API backend for the placement management system.

## Overview

This repository contains the backend for a placement platform built with Django and Django REST Framework. It includes:

- REST API endpoints for application workflows
- Django admin support
- CORS configuration for frontend apps
- SQLite for local development
- MySQL/TiDB support for production
- AI-related integrations via OpenAI/LangChain
- Static file handling with WhiteNoise

## Tech Stack

- Python 3.10+
- Django 4.x
- Django REST Framework
- MySQL / TiDB compatible database
- PostgreSQL-compatible driver support via psycopg2-binary
- OpenAI + LangChain integration
- Python-decouple for environment management
- CORS handling via django-cors-headers

## Repository Structure

```text
.
├── .env.example               # Example environment variables template
├── .gitignore                 # Ignore sensitive files and local artifacts
├── README.md                  # Project setup and usage documentation
├── manage.py                  # Django management entrypoint
├── requirements.txt           # Python dependencies
├── requirements-prod.txt      # Production dependency list
├── build_files.sh             # Build helper for deployment
├── vercel.json                # Vercel deployment config
├── main_app/                  # Application logic and API views
├── placement_django_backend/  # Django project settings and config
├── staticfiles_build/        # Generated static build output
├── wsgi.py                   # WSGI configuration
└── db.sqlite3                # Local SQLite database (ignored in production use)
```

## Prerequisites

Before setting up the project, make sure you have:

- Python 3.10 or newer
- pip
- virtualenv or venv
- Git
- A database available for local or production work

## Clone the Repository

```bash
git clone https://github.com/Shivam07042004/placement_backend.git
cd placement_backend
```

## Environment Setup

This project uses environment variables managed through a `.env` file. A sample file is already included as `.env.example`.

Create your local environment file:

```bash
cp .env.example .env
```

Then update the values in `.env` according to your environment.

Example configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True

MYSQLDATABASE=your_database_name
MYSQLUSER=your_db_user
MYSQLPASSWORD=your_db_password
MYSQLHOST=localhost
MYSQLPORT=3306

TIDB_DATABASE=your_tidb_database_name
TIDB_USERNAME=your_tidb_username
TIDB_PASSWORD=your_tidb_password
TIDB_HOST=your_tidb_gateway_host
TIDB_PORT=4000
TIDB_SSL_CA=
TIDB_SSL_DISABLE=False
DB_CONN_MAX_AGE=60

OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://aipipe.org/openai/v1
```

Important:

- Never commit your real `.env` or `.env.production` file.
- Keep secrets in local environment variables or your deployment platform secrets manager.
- The repository keeps a safe template in `.env.example` only.

## Install Dependencies

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or
.venv\Scripts\activate      # Windows
```

Install project dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Database Setup

### Local development

The project defaults to SQLite when `ENVIRONMENT` is not set to `production`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

No extra database setup is required for basic local development.

### Production / TiDB / MySQL

When `ENVIRONMENT=production`, the project reads database settings from the environment variables:

- `TIDB_DATABASE`
- `TIDB_USERNAME`
- `TIDB_PASSWORD`
- `TIDB_HOST`
- `TIDB_PORT`
- `TIDB_SSL_CA`
- `TIDB_SSL_DISABLE`

You can also use legacy fallback variables:

- `MYSQLDATABASE`
- `MYSQLUSER`
- `MYSQLPASSWORD`
- `MYSQLHOST`
- `MYSQLPORT`

## Run Migrations

```bash
python manage.py migrate
```

## Create a Superuser

```bash
python manage.py createsuperuser
```

## Start the Development Server

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## API Notes

The project includes Django REST Framework and token authentication. Some APIs may require authentication tokens depending on the app route.

## Static Files

Static files are configured with WhiteNoise.

```bash
python manage.py collectstatic
```

## Production Deployment

This project is compatible with deployment platforms such as:

- Vercel
- Railway
- standard Django hosting providers

Use environment variables from your deployment platform instead of committing secrets in the repository.

## Common Commands

```bash
# Start dev server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Check project status
python manage.py check
```

## Security Recommendations

- Do not commit `.env`, `.env.production`, or any secrets
- Rotate API keys if they were ever exposed
- Use environment-specific secrets on your hosting platform
- Keep `.env.example` as the only tracked template

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests and validation
5. Open a pull request

## License

This project does not currently define a repository license in the GitHub metadata. Add a license file if you want to publish the project under a formal open-source license.
