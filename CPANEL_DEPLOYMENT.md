# cPanel Deployment Guide

## Step-by-Step Deployment

### 1. Upload Files to cPanel

**Option A: File Manager**
1. Log into cPanel
2. Open **File Manager**
3. Navigate to `public_html` or create a subdirectory (e.g., `public_html/trivia-cards`)
4. Upload these files:
   - `app.py`
   - `card_generator_v2.py`
   - `passenger_wsgi.py`
   - `requirements-web.txt`
   - `templates/` folder (with index.html)
   - Any sample CSV files

**Option B: Git (if available)**
```bash
cd ~/public_html/trivia-cards
git clone https://github.com/YOUR-USERNAME/trivia-card-generator.git .
```

### 2. Set Up Python Application in cPanel

1. In cPanel, find **"Setup Python App"** or **"Python Selector"**
2. Click **"Create Application"**
3. Configure:
   - **Python version**: 3.9 or higher
   - **Application root**: `/home/username/public_html/trivia-cards`
   - **Application URL**: `/trivia-cards` (or your preferred URL)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

4. Click **"Create"**

### 3. Install Dependencies

**Option A: Through cPanel Interface**
1. In the Python App interface, find the **"Configuration"** section
2. Open the virtual environment
3. Install packages:
   ```bash
   pip install flask==3.0.0
   pip install reportlab==4.0.7
   pip install werkzeug==3.0.0
   ```

**Option B: Via SSH** (recommended)
```bash
# SSH into your server
ssh username@yourdomain.com

# Navigate to your app directory
cd ~/public_html/trivia-cards

# Activate virtual environment (path shown in cPanel Python App)
source /home/username/virtualenv/trivia-cards/3.9/bin/activate

# Install dependencies
pip install -r requirements-web.txt

# Exit
deactivate
```

### 4. Update passenger_wsgi.py

You may need to update the Python version in `passenger_wsgi.py`:
```python
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'trivia-cards', '3.11', 'bin', 'python3')
```
Change `'3.9'` to match your Python version (check in cPanel).

### 5. Set Permissions

```bash
# Via SSH
chmod 644 passenger_wsgi.py
chmod 644 app.py
chmod 644 card_generator_v2.py
chmod 755 templates
```

Or in cPanel File Manager:
- Right-click files → Change Permissions
- Set to 644 for files, 755 for directories

### 6. Configure .htaccess (if needed)

Create `.htaccess` in your app directory:
```apache
PassengerEnabled On
PassengerAppRoot /home/username/public_html/trivia-cards
PassengerBaseURI /trivia-cards
PassengerPython /home/username/virtualenv/trivia-cards/3.9/bin/python3
```

### 7. Restart Application

In cPanel's Python App interface:
- Click **"Restart"** or **"Stop/Start"**

Or via SSH:
```bash
touch ~/public_html/trivia-cards/passenger_wsgi.py
```

### 8. Test Your Application

Visit: `https://yourdomain.com/trivia-cards`

### 9. Set Environment Variables (Important!)

In cPanel Python App → **Configuration**:
```
SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=production
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Troubleshooting

### Error: "Internal Server Error"

**Check error logs:**
```bash
# Via SSH
tail -f ~/logs/yourdomain.com-error_log
```

Or in cPanel: **Errors** section

### Common Issues:

**1. Import errors**
- Solution: Make sure all dependencies are installed
```bash
source /home/username/virtualenv/trivia-cards/3.9/bin/activate
pip list  # Check installed packages
```

**2. Permission denied**
- Solution: Check file permissions (644 for files, 755 for dirs)

**3. Module not found**
- Solution: Verify virtual environment path in `passenger_wsgi.py`

**4. Can't write to temp directory**
- Solution: Check that temp directory is writable
```bash
chmod 755 /tmp
```

**5. 404 Not Found**
- Solution: Check `.htaccess` configuration and Application URL

### View Application Status

In cPanel Python App interface, check:
- Status: Should be "Running"
- URL: Should be accessible
- Logs: Check for errors

## Security Checklist for cPanel

- [ ] Set `SECRET_KEY` environment variable
- [ ] Disable directory browsing in `.htaccess`
- [ ] Set proper file permissions (644/755)
- [ ] Enable HTTPS (SSL certificate in cPanel)
- [ ] Configure firewall (if you have access)
- [ ] Regular backups enabled
- [ ] Keep Python packages updated

## Updating Your Application

```bash
# Via SSH
cd ~/public_html/trivia-cards
git pull  # If using git

# Or upload new files via File Manager

# Restart application
touch passenger_wsgi.py
```

## Performance Optimization

1. **Enable caching** in `.htaccess`:
```apache
<FilesMatch "\.(jpg|jpeg|png|gif|css|js)$">
  Header set Cache-Control "max-age=31536000, public"
</FilesMatch>
```

2. **Limit concurrent requests** - Configure in cPanel Python App settings

3. **Monitor resource usage** - Check cPanel → Metrics

## Getting Help

**cPanel-specific issues:**
- Contact your hosting provider
- Check cPanel documentation

**Application issues:**
- Check error logs: `~/logs/yourdomain.com-error_log`
- Check Python App logs in cPanel interface

## Alternative: Subdomain Setup

For a cleaner URL (e.g., `cards.yourdomain.com`):

1. Create subdomain in cPanel
2. Point it to `/home/username/public_html/trivia-cards`
3. Follow same setup steps above
4. Update `.htaccess` to use subdomain root
