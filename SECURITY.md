# Security Configuration and Best Practices

## Security Issues Fixed

### 1. ✅ File Upload Security
- **Filename sanitization**: Uses `secure_filename()` to prevent path traversal attacks
- **File type validation**: Checks both extension and content-type
- **File size limits**: 10MB max enforced by Flask
- **Temporary file handling**: Uses system temp directory with automatic cleanup

### 2. ✅ Information Disclosure
- **Error messages**: Sanitized in production (no stack traces exposed)
- **Debug mode**: Disabled by default, only enabled with explicit flag
- **Logging**: Errors logged server-side, generic messages to users

### 3. ✅ HTTP Security Headers
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Content-Security-Policy` - Restricts resource loading

### 4. ✅ Session Security
- **Secret key**: Auto-generated on startup
- **Localhost binding**: Development server binds to 127.0.0.1 by default

### 5. ✅ Input Validation
- CSV parsing validates structure and content
- Subject codes validated for uniqueness
- File content read as binary (no encoding issues)

## Remaining Considerations

### For Production Deployment:

1. **Rate Limiting** (RECOMMENDED):
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   
   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["100 per hour"]
   )
   
   @limiter.limit("10 per minute")
   @app.route('/api/generate', methods=['POST'])
   ```

2. **HTTPS Only** (REQUIRED for production):
   - Set up SSL/TLS certificates
   - Use a reverse proxy (nginx) with HTTPS
   - Enable HSTS header

3. **CORS Configuration** (if needed):
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": "https://yourdomain.com"}})
   ```

4. **Environment Variables**:
   ```python
   import os
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
   ```

5. **Database for Logs** (optional):
   - Consider logging to database or external service
   - Don't log sensitive user data

6. **Content Validation**:
   - Already implemented: validates CSV structure
   - Limits: 6 questions per card, specific format required
   - No arbitrary code execution possible

7. **Monitoring & Alerts**:
   - Monitor for unusual upload patterns
   - Alert on repeated errors
   - Track file sizes and processing time

## Known Safe Operations

- ✅ No file system traversal possible (uses temp files)
- ✅ No SQL injection (no database)
- ✅ No command injection (no shell commands executed)
- ✅ No code evaluation (no eval/exec)
- ✅ PDF generation sandboxed (ReportLab library)

## Testing Security

```bash
# Test file size limit
curl -X POST -F "csv=@large_file.csv" http://localhost:5000/api/generate

# Test invalid file types
curl -X POST -F "csv=@malicious.exe" http://localhost:5000/api/generate

# Test path traversal in filename
curl -X POST -F "csv=@../../etc/passwd" http://localhost:5000/api/generate
```

## Deployment Checklist

- [ ] Set `SECRET_KEY` environment variable
- [ ] Disable DEBUG mode (default is off)
- [ ] Use HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up monitoring/logging
- [ ] Use production WSGI server (gunicorn)
- [ ] Configure firewall rules
- [ ] Keep dependencies updated
- [ ] Regular security audits

## Update Dependencies

```bash
pip install --upgrade flask reportlab gunicorn
pip install flask-limiter  # For rate limiting
pip install flask-talisman  # For additional security headers
```

## Production Environment Variables

```bash
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"
export MAX_CONTENT_LENGTH=10485760  # 10MB
```
