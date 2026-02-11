# Django CRM System Deployment Guide

Deployment guide for CrmSys Django project to Debian 13 with PostgreSQL, Gunicorn, and Nginx.

**Target Server:** 192.168.116.106
**Domain:** https://crm.popymail.eu
**Local Access:** http://192.168.116.106:5000

---

## Prerequisites

- Debian 13 server with root/sudo access
- Domain DNS configured (A record for crm.popymail.eu pointing to 192.168.116.106)
- SSH access to the server

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
sudo apt install -y nginx certbot python3-certbot-nginx
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
pip install gunicorn
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
ALLOWED_HOSTS=crm.popymail.eu,192.168.116.106,localhost,127.0.0.1

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
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Add static root
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
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

## 9. Configure Gunicorn

### Create Gunicorn socket file:
```bash
sudo nano /etc/systemd/system/gunicorn_crm.socket
```

```ini
[Unit]
Description=Gunicorn socket for CRM

[Socket]
ListenStream=/run/gunicorn_crm.sock

[Install]
WantedBy=sockets.target
```

### Create Gunicorn service file:
```bash
sudo nano /etc/systemd/system/gunicorn_crm.service
```

```ini
[Unit]
Description=Gunicorn daemon for CRM System
Requires=gunicorn_crm.socket
After=network.target

[Service]
User=lenka
Group=www-data
WorkingDirectory=/var/www/CrmSys
Environment="PATH=/var/www/CrmSys/venv/bin"
ExecStart=/var/www/CrmSys/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn_crm.sock \
          CrmSys.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start and enable Gunicorn:
```bash
sudo systemctl start gunicorn_crm.socket
sudo systemctl enable gunicorn_crm.socket
sudo systemctl start gunicorn_crm.service
sudo systemctl enable gunicorn_crm.service
```

### Check status:
```bash
sudo systemctl status gunicorn_crm.socket
sudo systemctl status gunicorn_crm.service
```

---

## 10. Configure Nginx

### Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/crmsys
```

```nginx
# HTTP server for port 5000 (local IP access)
server {
    listen 192.168.116.106:5000;
    server_name 192.168.116.106;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/CrmSys/staticfiles/;
    }

    location /media/ {
        alias /var/www/CrmSys/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_crm.sock;
    }
}

# HTTP server for domain (will redirect to HTTPS)
server {
    listen 80;
    server_name crm.popymail.eu;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server for domain
server {
    listen 443 ssl http2;
    server_name crm.popymail.eu;

    # SSL certificates will be added by Certbot

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/CrmSys/staticfiles/;
    }

    location /media/ {
        alias /var/www/CrmSys/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_crm.sock;
    }

    client_max_body_size 10M;
}
```

### Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/crmsys /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 11. SSL Certificate Setup with Let's Encrypt

```bash
sudo certbot --nginx -d crm.popymail.eu
```

Follow the prompts to:
- Enter email address
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

### Set up automatic renewal:
```bash
sudo systemctl status certbot.timer
```

### Test renewal:
```bash
sudo certbot renew --dry-run
```

---

## 12. Set Permissions

```bash
sudo chown -R lenka:www-data /var/www/CrmSys
sudo chmod -R 755 /var/www/CrmSys
sudo chmod -R 775 /var/www/CrmSys/media
sudo chmod -R 775 /var/www/CrmSys/staticfiles
```

---

## 13. Firewall Configuration (Optional)

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw allow 5000/tcp
sudo ufw enable
sudo ufw status
```

---

## Verification

### Check all services are running:
```bash
sudo systemctl status gunicorn_crm.service
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Test access:
- **Domain:** https://crm.popymail.eu
- **Local IP:** http://192.168.116.106:5000

---

## Maintenance Commands

### View Gunicorn logs:
```bash
sudo journalctl -u gunicorn_crm.service -f
```

### View Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart services after code changes:
```bash
sudo systemctl restart gunicorn_crm.service
sudo systemctl restart nginx
```

### Update application:
```bash
cd /var/www/CrmSys
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn_crm.service
```

---

## Troubleshooting

### Check Gunicorn socket:
```bash
sudo systemctl status gunicorn_crm.socket
file /run/gunicorn_crm.sock
```

### Check permissions:
```bash
namei -nom /run/gunicorn_crm.sock
```

### Test Gunicorn manually:
```bash
cd /var/www/CrmSys
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 CrmSys.wsgi:application
```

### Database connection issues:
```bash
sudo -u postgres psql -d softmaker -c "SELECT 1;"
```

---

## Security Checklist

- [ ] Changed SECRET_KEY in .env
- [ ] Set DEBUG=False in production
- [ ] Configured ALLOWED_HOSTS correctly
- [ ] Database using strong password
- [ ] SSL certificate installed and working
- [ ] Firewall configured
- [ ] Regular backups scheduled (database and media files)
- [ ] Static and media files have correct permissions
- [ ] PostgreSQL only accepting local connections

---

## Backup Strategy

### Database backup:
```bash
sudo mkdir -p /var/backups/crmsys
sudo chown lenka:lenka /var/backups/crmsys
sudo -u postgres pg_dump softmaker > /var/backups/crmsys/crmsys_db_$(date +%Y%m%d).sql
```

### Full backup:
```bash
tar -czf /var/backups/crmsys/crmsys_full_$(date +%Y%m%d).tar.gz /var/www/CrmSys/media
```

### Automate with cron:
```bash
crontab -e
```
Add:
```cron
0 2 * * * sudo -u postgres pg_dump softmaker > /var/backups/crmsys/crmsys_db_$(date +\%Y\%m\%d).sql
```

---

## Notes

- The project uses Django 4.2.24 with Python 3.13
- PostgreSQL database is already configured in settings.py
- Environment variables are loaded from .env file using python-dotenv
- Database name: softmaker
- Database user: popov
- Deployment user: lenka (with sudo privileges)
- Project location: /var/www/CrmSys/
- Media files will be stored in /var/www/CrmSys/media/
- Static files will be collected to /var/www/CrmSys/staticfiles/
- Backups stored in /var/backups/crmsys/

---

**Deployment Date:** $(date)
**Django Version:** 4.2.24
**Python Version:** 3.13
