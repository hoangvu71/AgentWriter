# Security Guidelines

This guide covers security best practices, configurations, and fixes for BooksWriter deployment and development.

## 🛡️ Security Overview

BooksWriter implements multiple layers of security:
- **Environment variable protection** for sensitive credentials
- **Input validation and sanitization** across all inputs
- **Database security** with proper access controls
- **Content Security Policy (CSP)** for frontend protection
- **Audit trails** for all system activities

## 🔐 Authentication & Authorization

### Google Cloud Service Accounts

**Best Practices**:
1. **Use separate service accounts per environment**:
   ```bash
   # Development
   config/dev-service-account.json
   
   # Staging  
   config/staging-service-account.json
   
   # Production
   config/prod-service-account.json
   ```

2. **Principle of least privilege**:
   ```yaml
   # Required roles only:
   - roles/aiplatform.user      # For Vertex AI access
   - roles/ml.developer         # For ML operations
   ```

3. **Key rotation schedule**:
   ```bash
   # Rotate service account keys every 90 days
   gcloud iam service-accounts keys create new-key.json \
     --iam-account=service-account@project.iam.gserviceaccount.com
   ```

### Supabase Security

**Database Access Control**:
```sql
-- Enable Row Level Security for production
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE plots ENABLE ROW LEVEL SECURITY;
ALTER TABLE authors ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can only access their own data" 
ON users FOR ALL 
USING (auth.uid() = id);

CREATE POLICY "Users can only access their own sessions" 
ON sessions FOR ALL 
USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own plots" 
ON plots FOR ALL 
USING (auth.uid() = user_id);
```

**Access Token Management**:
```bash
# Use environment-specific tokens
SUPABASE_ANON_KEY_DEV=your_dev_anon_key
SUPABASE_ANON_KEY_PROD=your_prod_anon_key

# Service role tokens for admin operations only
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # Admin only
```

## 🔒 Environment Security

### Environment Variables

**Secure Configuration**:
```bash
# .env (development only - never commit)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_ACCESS_TOKEN=your-access-token
```

**Production Deployment**:
```bash
# Use system environment variables (not .env files)
export GOOGLE_CLOUD_PROJECT="production-project"
export SUPABASE_URL="https://prod.supabase.co"

# Or use secret management services
# AWS Secrets Manager, Google Secret Manager, etc.
```

**Security Checklist**:
- [ ] Never commit `.env` files to version control
- [ ] Use different credentials per environment
- [ ] Rotate credentials regularly (every 90 days)
- [ ] Use secret management services in production
- [ ] Audit credential access logs

### .gitignore Security
```bash
# Ensure these are in .gitignore
.env
.env.*
config/*.json
*.key
secrets/
credentials/
```

## 🌐 Web Security

### Content Security Policy (CSP)

**Current Implementation**:
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  connect-src 'self' ws: wss:;
  font-src 'self';
">
```

**Security Improvements Needed**:
1. **Remove 'unsafe-inline'** by moving inline styles to CSS files
2. **Add nonce-based CSP** for necessary inline scripts
3. **Implement Subresource Integrity (SRI)** for CDN resources

### Fixed Security Issues

#### 1. DOMPurify Integrity Hash Mismatch ✅
**Problem**: Incorrect SHA384 integrity hash caused library loading failures
**Solution**: 
```html
<!-- Current temporary fix -->
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>

<!-- Production fix needed -->
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"
        integrity="sha384-correct-hash-here"
        crossorigin="anonymous"></script>
```

**Action Required**: Generate correct hash using [SRI Hash Generator](https://www.srihash.org/)

#### 2. URL Validation Fixed ✅
**Problem**: `validateURL()` method rejected valid relative URLs
**Solution**: Updated validation to accept:
```javascript
// security.js - Fixed validation
function validateURL(url) {
    // Accept relative URLs
    if (url.startsWith('/') || url.startsWith('./')) {
        return true;
    }
    
    // Accept protocol-relative URLs
    if (url.startsWith('//')) {
        return true;
    }
    
    // Accept WebSocket protocols
    if (url.startsWith('ws://') || url.startsWith('wss://')) {
        return true;
    }
    
    // Validate absolute URLs
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}
```

#### 3. CSP Violations Temporarily Fixed ⚠️
**Problem**: Inline styles blocked by strict CSP
**Current Solution**: Added `'unsafe-inline'` to style-src (weakens security)
**Proper Solution Needed**: Move inline styles to CSS classes

**Inline Styles to Refactor**:
```html
<!-- templates/index.html:45 -->
<div id="parametersContent" style="display: none;">

<!-- templates/index.html:89 -->
<div id="selectedParams" style="background-color: #f0f0f0;">

<!-- templates/index.html:128 -->
<div id="typingIndicator" style="display: none;">
```

**Refactoring Plan**:
```css
/* static/css/main.css */
.parameters-content { display: none; }
.selected-params { background-color: #f0f0f0; }
.typing-indicator { display: none; }
.show { display: block !important; }
```

## 🔍 Input Validation

### Data Validation Patterns

**Pydantic Models for API Validation**:
```python
from pydantic import BaseModel, validator
from typing import Optional, List

class PlotRequest(BaseModel):
    title: str
    plot_summary: str
    genre: Optional[str] = None
    target_audience: Optional[dict] = None
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Title must be at least 3 characters')
        if len(v) > 200:
            raise ValueError('Title must be less than 200 characters')
        return v.strip()
    
    @validator('plot_summary') 
    def validate_plot_summary(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Plot summary must be at least 50 characters')
        if len(v) > 5000:
            raise ValueError('Plot summary must be less than 5000 characters')
        return v.strip()
```

**SQL Injection Prevention**:
```python
# Use parameterized queries (handled by adapters)
async def get_user_plots(self, user_id: str) -> List[dict]:
    query = "SELECT * FROM plots WHERE user_id = $1"
    return await self.execute_query(query, [user_id])

# Never use string formatting for SQL
# WRONG: f"SELECT * FROM plots WHERE user_id = '{user_id}'"
```

**XSS Prevention**:
```javascript
// Use DOMPurify for HTML sanitization
function sanitizeHTML(input) {
    return DOMPurify.sanitize(input, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
        ALLOWED_ATTR: []
    });
}

// Escape HTML in templates
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

## 📊 Database Security

### Connection Security

**Connection Pool Security**:
```python
# src/database/connection_pool.py
class SecureConnectionPool:
    def __init__(self, config):
        self.config = config
        # Use SSL for all connections
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        """Create secure SSL context for database connections"""
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
```

**UUID Security**:
```python
# Use cryptographically secure UUIDs
import uuid

def generate_secure_id() -> str:
    """Generate cryptographically secure UUID"""
    return str(uuid.uuid4())

# Always use string format for consistency
user_id = generate_secure_id()  # Returns string, not UUID object
```

### Data Encryption

**Sensitive Data Handling**:
```python
# Encrypt sensitive fields if needed
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

**Password Hashing** (if implementing user authentication):
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password securely"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

## 🔒 API Security

### Rate Limiting

**Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.route("/api/plots")
@limiter.limit("10/minute")
async def create_plot(request: Request):
    """Rate limited plot creation"""
    pass
```

### CORS Configuration

**Secure CORS Setup**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specific methods only
    allow_headers=["*"],
)
```

### Request Validation

**Size Limits**:
```python
from fastapi import HTTPException

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

async def validate_request_size(request: Request):
    """Validate request size"""
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > MAX_CONTENT_LENGTH:
        raise HTTPException(413, "Request too large")
```

## 🔐 MCP Security

### Access Control

**MCP Token Security**:
```json
{
  "servers": {
    "supabase": {
      "command": "npx",
      "args": ["@supabase/mcp-server-supabase@latest"],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}"
      }
    }
  }
}
```

**Security Considerations**:
- Use read-only access tokens when possible
- Limit MCP access to development/staging environments
- Audit all MCP operations
- Never expose MCP tokens in logs

### Query Validation

**Safe MCP Queries**:
```python
# Validate MCP queries before execution
def validate_mcp_query(query: str) -> bool:
    """Validate MCP query for safety"""
    dangerous_keywords = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 
        'CREATE', 'INSERT', 'UPDATE'
    ]
    
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False
    
    return True
```

## 📋 Security Checklist

### Development Environment
- [ ] Environment variables not committed to git
- [ ] Service account keys stored securely
- [ ] Debug logging disabled in production
- [ ] Development databases isolated from production

### Production Deployment
- [ ] HTTPS enabled with valid certificates
- [ ] Environment variables managed by secret service
- [ ] Row Level Security enabled on all user tables
- [ ] Rate limiting configured on all API endpoints
- [ ] CORS configured with specific origins
- [ ] Content Security Policy implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection protection verified
- [ ] XSS protection implemented
- [ ] Error messages don't expose sensitive information

### Database Security
- [ ] Connection encryption enabled
- [ ] Access tokens rotated regularly
- [ ] Database backups encrypted
- [ ] Audit logging enabled
- [ ] User access reviewed regularly

### Monitoring & Auditing
- [ ] Security event logging enabled
- [ ] Failed authentication attempts monitored
- [ ] Unusual access patterns alerted
- [ ] Dependency vulnerabilities scanned
- [ ] Security patch schedule established

## 🚨 Incident Response

### Security Incident Procedure

1. **Immediate Response**:
   ```bash
   # Isolate the system
   # Change all credentials
   # Review access logs
   # Document the incident
   ```

2. **Investigation**:
   ```bash
   # Analyze logs for breach scope
   grep "SECURITY\|ERROR\|FAILED" logs/security.log
   
   # Check database access patterns
   SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours';
   ```

3. **Recovery**:
   ```bash
   # Patch vulnerabilities
   # Restore from clean backups if needed
   # Update security measures
   # Monitor for additional threats
   ```

### Emergency Contacts
- **Development Team**: [Contact information]
- **Security Team**: [Contact information]  
- **Infrastructure Team**: [Contact information]

## 🔮 Future Security Enhancements

### Planned Improvements

1. **Enhanced CSP**:
   - Remove all 'unsafe-inline' directives
   - Implement nonce-based CSP
   - Add reporting endpoints

2. **Authentication System**:
   - Multi-factor authentication
   - OAuth2 integration
   - Session management

3. **Advanced Monitoring**:
   - Security Information and Event Management (SIEM)
   - Real-time threat detection
   - Automated incident response

4. **Compliance**:
   - SOC 2 Type II certification
   - GDPR compliance enhancements
   - Regular security audits

## 📚 Security Resources

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [Supabase Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

### Internal Documentation
- [Architecture Overview](../architecture/overview.md) - Security architecture
- [Environment Configuration](../setup/environment.md) - Secure configuration  
- [Troubleshooting Guide](troubleshooting.md) - Security issue resolution

---

Security is an ongoing process. Regular reviews, updates, and monitoring ensure BooksWriter maintains a strong security posture while supporting development velocity and user needs.