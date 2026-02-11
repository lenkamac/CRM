# Alternative Django CRM Deployment Guide (Local Network Only)

Simplified deployment for CrmSys to Debian 13 with PostgreSQL, Gunicorn, and Nginx - accessible via local IP address only.

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
sudo apt install -y nginx
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

## 10. Configure Nginx (HTTP Only)

### Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/crmsys
```

```nginx
# HTTP server for local network access
server {
    listen 80;
    server_name 192.168.116.106;

    client_max_body_size 10M;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias /var/www/CrmSys/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/CrmSys/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_crm.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/crmsys /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 11. Set Permissions

```bash
sudo chown -R lenka:www-data /var/www/CrmSys
sudo chmod -R 755 /var/www/CrmSys
sudo chmod -R 775 /var/www/CrmSys/media
sudo chmod -R 775 /var/www/CrmSys/staticfiles
```

---

## 12. Firewall Configuration (Optional)

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
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
Open a web browser on any device in your local network and navigate to:
- **http://192.168.116.106**

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

# Transfer new files from local machine first
# Then on server:
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

### Test from local machine:
```bash
curl http://192.168.116.106
```

### Database connection issues:
```bash
sudo -u postgres psql -d softmaker -c "SELECT 1;"
```

### Check Nginx configuration:
```bash
sudo nginx -t
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

### Automate with cron:
```bash
crontab -e
```
Add:
```cron
0 2 * * * sudo -u postgres pg_dump softmaker > /var/backups/crmsys/crmsys_db_$(date +\%Y\%m\%d).sql
0 3 * * 0 tar -czf /var/backups/crmsys/crmsys_media_$(date +\%Y\%m\%d).tar.gz /var/www/CrmSys/media
```

---

## Security Notes for Local Network Deployment

⚠️ **Important:** This deployment is suitable for local network use only. If you plan to expose this application to the internet in the future, you MUST:

1. Obtain and configure SSL certificates (Let's Encrypt)
2. Enable HTTPS-only access
3. Update Django security settings:
   - Set `SECURE_SSL_REDIRECT = True`
   - Set `SESSION_COOKIE_SECURE = True`
   - Set `CSRF_COOKIE_SECURE = True`
4. Configure proper firewall rules
5. Implement rate limiting
6. Regular security updates

---

## Summary

- **Access URL:** http://192.168.116.106
- **Database:** PostgreSQL (softmaker)
- **Application Server:** Gunicorn
- **Web Server:** Nginx
- **Python Version:** 3.13
- **Django Version:** 4.2.24
- **No SSL/HTTPS** (HTTP only for local network)
- **No domain name required**

---

**Key Differences from Domain-Based Deployment:**
1. No Certbot/SSL certificate installation
2. Simplified Nginx configuration (single HTTP server block)
3. Disabled SSL-related Django security settings
4. Access via IP address only
5. No DNS configuration required
6. Firewall allows only port 80 (and SSH)
