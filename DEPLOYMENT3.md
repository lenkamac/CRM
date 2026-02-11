# Django CRM Deployment Guide - Apache with mod_wsgi (Local Network Only)

Deployment guide for CrmSys to Debian 13 with PostgreSQL and Apache web server using mod_wsgi - accessible via local IP address only.

**Target Server:** 192.168.116.106
**Access URL:** http://192.168.116.106

---

## Prerequisites

- Debian 13 server with root/sudo access
- SSH access to the server
- Local network connectivity

---

## 1. Server Setup and System Packages

### Connect to the server:
```bash
ssh lenka@192.168.116.106
```

### Update system and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y postgresql postgresql-contrib libpq-dev
sudo apt install -y apache2 apache2-dev libapache2-mod-wsgi-py3
sudo apt install -y git curl
```

---

## 2. PostgreSQL Database Setup

### Switch to postgres user and create database:
```bash
sudo -u postgres psql
```

### In PostgreSQL prompt, run:
```sql
CREATE DATABASE softmaker;
CREATE USER popov WITH PASSWORD 'your_secure_password_here';
ALTER ROLE popov SET client_encoding TO 'utf8';
ALTER ROLE popov SET default_transaction_isolation TO 'read committed';
ALTER ROLE popov SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE softmaker TO popov;
\q
```

---

## 3. Create Project Directory

### As lenka user on the server:
```bash
sudo mkdir -p /var/www/CrmSys
sudo chown -R lenka:lenka /var/www/CrmSys
```

---

## 4. Transfer Project Files

### On your local machine:
```bash
cd /home/lenka/PycharmProjects/PythonProject
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='media/*' --exclude='db.sqlite3' CrmSys/ lenka@192.168.116.106:/var/www/CrmSys/
```

---

## 5. Server-Side Project Setup

### On the server (as lenka user):
```bash
cd /var/www/CrmSys

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Configure Environment Variables

### Create .env file:
```bash
nano /var/www/CrmSys/.env
```

### Add the following content:
```env
SECRET_KEY=your_new_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=192.168.116.106,localhost,127.0.0.1

DATABASE_NAME=softmaker
DATABASE_USER=popov
DATABASE_PASSWORD=your_secure_password_here
```

**Note:** Generate a new SECRET_KEY using:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 7. Update Django Settings for Production

### Edit settings.py:
```bash
nano /var/www/CrmSys/CrmSys/settings.py
```

### Update the following sections:

```python
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Add static root
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Security settings (without SSL since we're using HTTP)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# DO NOT enable these for HTTP-only deployment:
# SECURE_SSL_REDIRECT = False
# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False
```

---

## 8. Run Django Setup Commands

```bash
cd /var/www/CrmSys
source venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

## 9. Create WSGI Configuration File

### Create wsgi.py wrapper script (if needed):
```bash
nano /var/www/CrmSys/CrmSys/wsgi.py
```

Verify it contains:
```python
import os
import sys

# Add the project directory to the sys.path
path = '/var/www/CrmSys'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CrmSys.settings')

# Load environment variables from .env file
from pathlib import Path
env_file = Path('/var/www/CrmSys/.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## 10. Configure Apache

### Create Apache virtual host configuration:
```bash
sudo nano /etc/apache2/sites-available/crmsys.conf
```

```apache
<VirtualHost *:80>
    ServerName 192.168.116.106
    ServerAdmin lenka@localhost

    DocumentRoot /var/www/CrmSys

    # Python virtual environment
    WSGIDaemonProcess crmsys python-home=/var/www/CrmSys/venv python-path=/var/www/CrmSys
    WSGIProcessGroup crmsys
    WSGIScriptAlias / /var/www/CrmSys/CrmSys/wsgi.py

    # WSGI configuration
    <Directory /var/www/CrmSys/CrmSys>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # Static files
    Alias /static /var/www/CrmSys/staticfiles
    <Directory /var/www/CrmSys/staticfiles>
        Require all granted
        Options -Indexes
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </Directory>

    # Media files
    Alias /media /var/www/CrmSys/media
    <Directory /var/www/CrmSys/media>
        Require all granted
        Options -Indexes
    </Directory>

    # Error and Access logs
    ErrorLog ${APACHE_LOG_DIR}/crmsys_error.log
    CustomLog ${APACHE_LOG_DIR}/crmsys_access.log combined

    # Security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

### Enable required Apache modules:
```bash
sudo a2enmod wsgi
sudo a2enmod headers
sudo a2enmod expires
```

### Disable default site and enable CRM site:
```bash
sudo a2dissite 000-default.conf
sudo a2ensite crmsys.conf
```

### Test Apache configuration:
```bash
sudo apache2ctl configtest
```

### Restart Apache:
```bash
sudo systemctl restart apache2
```

---

## 11. Set Permissions

```bash
# Set ownership
sudo chown -R lenka:www-data /var/www/CrmSys

# Set directory permissions
sudo chmod -R 755 /var/www/CrmSys

# Set special permissions for media and static files
sudo chmod -R 775 /var/www/CrmSys/media
sudo chmod -R 775 /var/www/CrmSys/staticfiles

# Allow Apache to write to media directory
sudo chown -R www-data:www-data /var/www/CrmSys/media

# Secure .env file
sudo chmod 600 /var/www/CrmSys/.env
sudo chown lenka:www-data /var/www/CrmSys/.env
```

---

## 12. Firewall Configuration (Optional)

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Apache'
sudo ufw enable
sudo ufw status
```

---

## Verification

### Check Apache status:
```bash
sudo systemctl status apache2
```

### Check PostgreSQL status:
```bash
sudo systemctl status postgresql
```

### Test access:
Open a web browser on any device in your local network and navigate to:
- **http://192.168.116.106**

---

## Maintenance Commands

### View Apache error logs:
```bash
sudo tail -f /var/log/apache2/crmsys_error.log
```

### View Apache access logs:
```bash
sudo tail -f /var/log/apache2/crmsys_access.log
```

### Restart Apache after code changes:
```bash
sudo systemctl restart apache2
```

### Reload Apache (graceful restart):
```bash
sudo systemctl reload apache2
```

### Update application:
```bash
cd /var/www/CrmSys
source venv/bin/activate

# Transfer new files from local machine first
# Then on server:
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart apache2
```

---

## Troubleshooting

### Check Apache configuration syntax:
```bash
sudo apache2ctl configtest
```

### Check loaded Apache modules:
```bash
apache2ctl -M | grep wsgi
```

### Test Python import in virtual environment:
```bash
cd /var/www/CrmSys
source venv/bin/activate
python -c "import django; print(django.get_version())"
```

### Check WSGI module:
```bash
dpkg -l | grep libapache2-mod-wsgi-py3
```

### Verify file permissions:
```bash
ls -la /var/www/CrmSys/
ls -la /var/www/CrmSys/CrmSys/wsgi.py
```

### Test database connection:
```bash
sudo -u postgres psql -d softmaker -c "SELECT 1;"
```

### Check Apache process and user:
```bash
ps aux | grep apache2
```

### Manually test Django:
```bash
cd /var/www/CrmSys
source venv/bin/activate
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

### View all Apache logs:
```bash
sudo tail -f /var/log/apache2/*.log
```

---

## Common Issues and Solutions

### Issue: 500 Internal Server Error

**Solution 1 - Check permissions:**
```bash
sudo chown -R www-data:www-data /var/www/CrmSys/media
sudo chmod -R 775 /var/www/CrmSys/media
```

**Solution 2 - Check .env file loading:**
Make sure wsgi.py loads environment variables correctly.

**Solution 3 - Check logs:**
```bash
sudo tail -50 /var/log/apache2/crmsys_error.log
```

### Issue: Static files not loading

**Solution:**
```bash
cd /var/www/CrmSys
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart apache2
```

### Issue: Permission denied errors

**Solution:**
```bash
sudo chown -R lenka:www-data /var/www/CrmSys
sudo chmod -R 755 /var/www/CrmSys
sudo chmod -R 775 /var/www/CrmSys/media
```

### Issue: ModuleNotFoundError

**Solution - Verify virtual environment in Apache config:**
```bash
# Check that python-home points to correct venv
sudo nano /etc/apache2/sites-available/crmsys.conf
# Restart Apache
sudo systemctl restart apache2
```

---

## Backup Strategy

### Database backup:
```bash
sudo mkdir -p /var/backups/crmsys
sudo chown lenka:lenka /var/backups/crmsys
sudo -u postgres pg_dump softmaker > /var/backups/crmsys/crmsys_db_$(date +%Y%m%d).sql
```

### Media files backup:
```bash
tar -czf /var/backups/crmsys/crmsys_media_$(date +%Y%m%d).tar.gz /var/www/CrmSys/media
```

### Full backup script:
```bash
nano /home/lenka/backup_crm.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/crmsys"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
sudo -u postgres pg_dump softmaker > "$BACKUP_DIR/crmsys_db_$DATE.sql"

# Media files backup
tar -czf "$BACKUP_DIR/crmsys_media_$DATE.tar.gz" /var/www/CrmSys/media

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "crmsys_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
chmod +x /home/lenka/backup_crm.sh
```

### Automate with cron:
```bash
crontab -e
```
Add:
```cron
0 2 * * * /home/lenka/backup_crm.sh >> /var/log/crmsys_backup.log 2>&1
```

---

## Performance Tuning

### Increase Apache worker processes:
```bash
sudo nano /etc/apache2/mods-available/mpm_prefork.conf
```

```apache
<IfModule mpm_prefork_module>
    StartServers             5
    MinSpareServers          5
    MaxSpareServers         10
    MaxRequestWorkers      150
    MaxConnectionsPerChild   0
</IfModule>
```

### Configure WSGI processes:
Edit `/etc/apache2/sites-available/crmsys.conf`:
```apache
WSGIDaemonProcess crmsys python-home=/var/www/CrmSys/venv python-path=/var/www/CrmSys processes=3 threads=10 display-name=%{GROUP}
```

Restart Apache:
```bash
sudo systemctl restart apache2
```

---

## Security Notes for Local Network Deployment

⚠️ **Important:** This deployment is suitable for local network use only. If you plan to expose this application to the internet in the future, you MUST:

1. Obtain and configure SSL certificates (Let's Encrypt with mod_ssl)
2. Enable HTTPS-only access
3. Update Django security settings:
   - Set `SECURE_SSL_REDIRECT = True`
   - Set `SESSION_COOKIE_SECURE = True`
   - Set `CSRF_COOKIE_SECURE = True`
4. Configure proper firewall rules
5. Implement rate limiting with mod_evasive or fail2ban
6. Regular security updates
7. Enable Apache security modules (mod_security)

---

## Summary

- **Access URL:** http://192.168.116.106
- **Database:** PostgreSQL (softmaker)
- **Web Server:** Apache 2.4 with mod_wsgi
- **Python Version:** 3.13
- **Django Version:** 4.2.24
- **No SSL/HTTPS** (HTTP only for local network)
- **No domain name required**

---

## Key Differences from Nginx/Gunicorn Deployment:

1. **Apache with mod_wsgi** instead of Nginx + Gunicorn
2. **Direct Python integration** via mod_wsgi (no separate application server)
3. **Single service** to manage (Apache handles everything)
4. **Different configuration files** (.conf instead of systemd services)
5. **Built-in static file serving** (no need for separate proxy configuration)

---

## Advantages of Apache + mod_wsgi:

- ✅ Simpler architecture (one service instead of two)
- ✅ Mature and well-documented
- ✅ Built-in process management
- ✅ Excellent static file handling
- ✅ Easy to configure virtual hosts
- ✅ Widely used in enterprise environments

---

**Deployment Date:** February 10, 2026
**Django Version:** 4.2.24
**Python Version:** 3.13
**Apache Version:** 2.4+
