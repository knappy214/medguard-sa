# MedGuard SA Database Setup Guide

This guide will help you set up PostgreSQL for the MedGuard SA Wagtail CMS project.

## Prerequisites

1. **PostgreSQL installed and running**
   - Download from: https://www.postgresql.org/download/
   - Ensure the PostgreSQL service is running
   - You should be able to connect as the `postgres` superuser

2. **Python 3.8+ installed**
   - Download from: https://www.python.org/downloads/
   - Ensure `pip` is available

3. **Database created**
   - Create a database named `medguard_sa` in PostgreSQL
   - You can do this via pgAdmin or command line:
   ```sql
   CREATE DATABASE medguard_sa;
   ```

## Quick Setup (Recommended)

### Option 1: Automated Setup Script

1. **Run the setup script:**
   ```bash
   cd medguard_backend
   chmod +x setup_db.sh
   ./setup_db.sh
   ```

2. **Follow the prompts:**
   - Enter your PostgreSQL superuser password when prompted
   - The script will create a secure user and generate a `.env` file

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

2. **Run the PostgreSQL setup:**
   ```bash
   python3 setup_postgres.py
   ```

3. **Follow the prompts and save the generated password**

## Manual Database User Creation

If you prefer to create the database user manually:

1. **Connect to PostgreSQL as superuser:**
   ```bash
   psql -U postgres -h localhost
   ```

2. **Create the user:**
   ```sql
   CREATE USER medguard_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE medguard_sa TO medguard_user;
   \c medguard_sa
   GRANT ALL ON SCHEMA public TO medguard_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medguard_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO medguard_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO medguard_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO medguard_user;
   ```

3. **Create a `.env` file in the `medguard_backend` directory:**
   ```env
   # Database Configuration
   DB_NAME=medguard_sa
   DB_USER=medguard_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432

   # Django Configuration
   SECRET_KEY=your_secure_secret_key_here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Wagtail Configuration
   WAGTAILADMIN_BASE_URL=http://localhost:8000
   ```

## Post-Setup Steps

After the database is configured:

1. **Navigate to the CMS directory:**
   ```bash
   cd medguard_cms
   ```

2. **Install all project dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

3. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser for Wagtail admin:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the Wagtail admin:**
   - Open your browser and go to: http://localhost:8000/admin
   - Log in with the superuser credentials you created

## Environment Variables

The following environment variables are used by the application:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_NAME` | Database name | `medguard_sa` |
| `DB_USER` | Database username | `medguard_user` |
| `DB_PASSWORD` | Database password | (generated) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `SECRET_KEY` | Django secret key | (generated) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `WAGTAILADMIN_BASE_URL` | Wagtail admin base URL | `http://localhost:8000` |

## Security Notes

1. **Never commit the `.env` file to version control**
   - Add `.env` to your `.gitignore` file
   - Keep the file secure and backed up

2. **Use strong passwords in production**
   - Change the default `SECRET_KEY`
   - Use a strong database password
   - Set `DEBUG=False` in production

3. **Database permissions**
   - The `medguard_user` has full access to the `medguard_sa` database
   - In production, consider using more restrictive permissions

## Troubleshooting

### Connection Issues

1. **PostgreSQL not running:**
   ```bash
   # On Windows
   net start postgresql-x64-15
   
   # On macOS
   brew services start postgresql
   
   # On Linux
   sudo systemctl start postgresql
   ```

2. **Authentication failed:**
   - Check your PostgreSQL password
   - Ensure the `postgres` user exists and has the correct password

3. **Database does not exist:**
   ```sql
   CREATE DATABASE medguard_sa;
   ```

### Permission Issues

1. **User already exists:**
   ```sql
   DROP USER IF EXISTS medguard_user;
   ```

2. **Permission denied:**
   - Ensure you're connecting as the `postgres` superuser
   - Check that the user has the correct permissions

### Python/Django Issues

1. **Module not found:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Migration errors:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Support

If you encounter issues:

1. Check the PostgreSQL logs for database-related errors
2. Ensure all dependencies are installed correctly
3. Verify the `.env` file is in the correct location
4. Test the database connection manually

For additional help, refer to:
- [Django Database Documentation](https://docs.djangoproject.com/en/stable/ref/databases/)
- [Wagtail Documentation](https://docs.wagtail.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) 