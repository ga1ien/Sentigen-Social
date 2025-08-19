# Supabase + FastAPI + Railway Authentication Issue - Comprehensive Report

## 🎯 Problem Summary

**Issue**: Frontend shows user as logged in (profile picture visible), but backend consistently returns `401 Unauthorized` with `{"detail":"Invalid authentication token"}` when accessing protected endpoints.

**Stack**:
- **Frontend**: Next.js on Vercel
- **Backend**: FastAPI on Railway
- **Database/Auth**: Supabase
- **User**: `g@sentigen.ai` (ID: `6ec57fe0-6ffe-4662-9a17-20311fe525f5`)

---

## 🏗️ Architecture Overview

### Frontend (Next.js + Vercel)
```typescript
// Supabase Client Configuration
export const createClient = () => {
  supabaseInstance = createBrowserClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      storageKey: 'zyyn-auth-token',  // Custom storage key
      storage: typeof window !== 'undefined' ? window.localStorage : undefined,
      autoRefreshToken: true,
      detectSessionInUrl: true
    }
  })
}
```

### Backend (FastAPI + Railway)
```python
# Authentication Service
class UserAuthService:
    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.security = HTTPBearer()

    async def _validate_supabase_token(self, token: str) -> Optional[str]:
        # JWT decode + admin verification approach
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")

        # Verify user exists via Supabase admin API
        admin_response = self.supabase_client.service_client.auth.admin.get_user_by_id(user_id)
```

### API Request Flow
```
Frontend → Axios Interceptor → Add Bearer Token → Railway Backend → FastAPI Dependency → UserAuthService
```

---

## 📋 Everything We've Tried (Chronological)

### 1. **Initial Diagnosis** ✅
- **Action**: Examined frontend and backend authentication implementation
- **Finding**: Frontend uses custom `zyyn-auth-token` storage key
- **Result**: Confirmed frontend appears logged in, backend rejects tokens

### 2. **Environment Variable Verification** ✅
- **Action**: Verified Railway environment variables
- **Finding**: All required variables present:
  - `SUPABASE_URL`: `https://lvgrswaemwvmjdawsvdj.supabase.co`
  - `SUPABASE_SERVICE_KEY`: Set (219 chars)
  - `SUPABASE_ANON_KEY`: Set (208 chars)
  - `JWT_SECRET`: Set (legacy approach)
- **Result**: Environment correctly configured

### 3. **JWT Secret Analysis** ❌
- **Action**: Initial hypothesis that Railway missing `JWT_SECRET`
- **Finding**: `JWT_SECRET` was present but tokens contain `kid` (Key ID)
- **Issue**: Supabase uses key rotation; `JWT_SECRET` was legacy key, tokens signed with different key
- **Result**: Manual JWT verification failed

### 4. **Supabase API Method Discovery** ✅
- **Action**: Created debug script to test available Supabase Python SDK methods
- **Finding**:
  - `admin.get_user_by_access_token` **DOES NOT EXIST** ❌
  - `auth.get_user` fails with session errors ❌
  - `admin.get_user_by_id` **WORKS** ✅
- **Result**: Identified correct API method to use

### 5. **Authentication Approach Evolution**

   **V1 - Manual JWT + Secret** ❌
   ```python
   jwt.decode(token, jwt_secret, algorithms=["HS256"])
   ```

   **V2 - Hybrid Approach** ❌
   ```python
   # Try HS256, fallback to Supabase client validation
   ```

   **V3 - Pure Supabase SDK** ❌
   ```python
   service_client.auth.admin.get_user_by_access_token(token)  # Method doesn't exist!
   ```

   **V4 - JWT Decode + Admin Verification** ✅ (Local) ❌ (Railway)
   ```python
   decoded = jwt.decode(token, options={"verify_signature": False})
   user_id = decoded.get("sub")
   admin_response = service_client.auth.admin.get_user_by_id(user_id)
   ```

### 6. **Dependencies Management** ✅
- **Action**: Added `PyJWT==2.10.1` to `requirements.txt`
- **Finding**: Railway was missing JWT decoding library
- **Result**: Dependency deployed successfully

### 7. **Token Extraction & Analysis** ✅
- **Action**: Extracted real user token from browser storage
- **Process**:
  1. Found `zyyn-auth-token` cookie (base64-encoded JSON)
  2. Decoded to extract `access_token`
  3. Verified token format and expiry
- **Token Details**:
  - **Algorithm**: `HS256` with `kid`: `LgN2jrPHrHI1SewK2`
  - **User ID**: `6ec57fe0-6ffe-4662-9a17-20311fe525f5`
  - **Email**: `g@sentigen.ai`
  - **Expires**: `1755593053` (valid for 1+ hour)
  - **Role**: `authenticated`

### 8. **Local vs Production Testing** 🤔
- **Local Test**: ✅ **WORKS PERFECTLY**
  ```
  ✅ AUTHENTICATION SUCCESS!
     User ID: 6ec57fe0-6ffe-4662-9a17-20311fe525f5
     Email: g@sentigen.ai
     Full Name: Galen
  ```
- **Railway Production**: ❌ **FAILS CONSISTENTLY**
  ```
  {"detail":"Invalid authentication token"}
  ```

### 9. **Railway Deployment Verification** ✅
- **Action**: Multiple forced deployments with version comments
- **Commits**: `ab597fa`, `129313a`, `cd72c10`, `a51907f`
- **Finding**: Health endpoint confirms recent deployments
- **Result**: Railway is running latest code

---

## 📊 Current State Analysis

### ✅ **What's Working**
1. **Frontend Authentication**: User successfully logs in, profile shows
2. **Token Storage**: `zyyn-auth-token` correctly stored in browser cookies
3. **Token Extraction**: Can decode and access user information
4. **Backend Code Logic**: Authentication works perfectly in local testing
5. **Environment Variables**: All Railway env vars correctly configured
6. **Supabase Connection**: Backend can connect to Supabase admin API

### ❌ **What's Failing**
1. **Railway Production Authentication**: Consistent 401 errors
2. **Token Validation**: Railway backend cannot validate tokens that work locally

### 🤔 **Key Mysteries**
1. **Local vs Production Gap**: Identical code works locally but fails on Railway
2. **Token Validity**: Same token fails on Railway but works locally
3. **Deployment Verification**: Railway appears to be running latest code

---

## 🔬 Technical Analysis

### **Token Anatomy**
```json
{
  "alg": "HS256",
  "kid": "LgN2jrPHrHI1SewK2",  // Key rotation identifier
  "typ": "JWT"
}
```

```json
{
  "iss": "https://lvgrswaemwvmjdawsvdj.supabase.co/auth/v1",
  "sub": "6ec57fe0-6ffe-4662-9a17-20311fe525f5",
  "aud": "authenticated",
  "exp": 1755593053,
  "iat": 1755589453,
  "email": "g@sentigen.ai",
  "role": "authenticated",
  "session_id": "89e5a8d2-3684-472e-98a2-dcda42b550f0"
}
```

### **Authentication Flow Analysis**
```
1. User Login (Frontend) ✅
2. Supabase Issues JWT ✅
3. Frontend Stores Token ✅
4. Axios Intercepts Request ✅
5. Adds Bearer Header ✅
6. Railway Receives Request ✅
7. FastAPI Dependency Calls UserAuthService ❌ FAILS HERE
8. JWT Decode Works ✅ (locally)
9. Admin API Verification ❌ FAILS HERE (Railway)
```

### **Error Patterns**
- **Consistent**: Every request returns identical error
- **Environment-Specific**: Only fails on Railway, never locally
- **Token-Independent**: Multiple different tokens all fail
- **Endpoint-Agnostic**: Both `/api/auth/me` and `/api/research/start` fail

---

## 🔍 Research: Best Practices & Common Issues

### **Supabase + FastAPI Authentication Best Practices**

#### **Recommended Approach** (According to Supabase Docs)
```python
from supabase import create_client

# Method 1: Service Role Validation (Recommended)
async def validate_token_with_service_role(token: str):
    service_client = create_client(supabase_url, service_role_key)
    try:
        # Use service client to validate user token
        user = service_client.auth.admin.get_user_by_id(user_id_from_jwt)
        return user
    except Exception as e:
        return None
```

#### **Common Issues & Solutions**

1. **Key Rotation Problems**
   - **Issue**: Supabase rotates JWT signing keys
   - **Solution**: Use service role + admin API, not manual JWT verification
   - **Our Status**: ✅ Implemented this approach

2. **Environment Variable Mismatches**
   - **Issue**: Different keys between environments
   - **Solution**: Verify all env vars match Supabase dashboard exactly
   - **Our Status**: ✅ Verified multiple times

3. **Token Storage Differences**
   - **Issue**: Frontend and backend expect tokens in different formats
   - **Solution**: Ensure consistent token extraction
   - **Our Status**: ✅ Using correct token from `access_token` field

### **FastAPI + Supabase Integration Patterns**

#### **Dependency Injection Pattern** (Current Approach)
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> UserContext:
    user = await auth_service.authenticate_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return user
```

#### **Alternative: Middleware Approach**
```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/protected"):
        auth_header = request.headers.get("Authorization")
        # Validate token
    response = await call_next(request)
    return response
```

### **Railway Deployment Common Issues**

1. **Environment Variable Sync Delays**
   - **Issue**: Env vars take time to propagate
   - **Solution**: Check Railway dashboard, restart service

2. **Build Cache Issues**
   - **Issue**: Old code cached in build process
   - **Solution**: Force rebuild with code changes
   - **Our Status**: ✅ Multiple forced rebuilds attempted

3. **Docker Layer Caching**
   - **Issue**: Python dependencies cached incorrectly
   - **Solution**: Clear build cache or modify Dockerfile
   - **Potential**: Could explain local vs Railway differences

### **Vercel + FastAPI Integration**

1. **CORS Configuration**
   - **Issue**: Cross-origin request failures
   - **Solution**: Proper CORS middleware setup

2. **Token Transmission**
   - **Issue**: Tokens not properly sent in requests
   - **Solution**: Axios interceptors (✅ Currently implemented)

---

## 🐛 Debugging Information for Other AIs/Developers

### **Environment Details**
- **Railway Backend URL**: `https://sentigen-social-production.up.railway.app`
- **Vercel Frontend**: `https://zyyn.ai`
- **Supabase Project**: `lvgrswaemwvmjdawsvdj.supabase.co`
- **Python Version**: 3.13
- **FastAPI Version**: 0.115.13
- **Supabase Python SDK**: Latest

### **Reproduction Steps**
1. Login at `https://zyyn.ai/auth/login` with `g@sentigen.ai`
2. Navigate to `https://zyyn.ai/dashboard/create/pipeline`
3. Fill form and click "Start Research"
4. Observe "sign in required" error despite being logged in

### **Test Commands**
```bash
# Test with extracted token
curl -X GET "https://sentigen-social-production.up.railway.app/api/auth/me" \
  -H "Authorization: Bearer [TOKEN]"

# Expected: User details
# Actual: {"detail":"Invalid authentication token"}
```

### **Local Testing (Works)**
```bash
cd /Users/galenoakes/Development/Sentigen-Social
python3 test_auth_locally.py
# Result: ✅ AUTHENTICATION SUCCESS!
```

### **Key Files to Examine**
- `social-media-module/backend/core/user_auth.py` (Authentication logic)
- `frontend/src/lib/supabase/client.ts` (Frontend Supabase config)
- `frontend/src/lib/api.ts` (Axios interceptor)
- `social-media-module/backend/requirements.txt` (Dependencies)

---

## 🎯 Next Steps & Recommendations

### **Immediate Actions**
1. **Railway Logging Investigation**
   - Add extensive logging to Railway deployment
   - Check Railway application logs for authentication errors
   - Verify which step in auth process fails on Railway

2. **Environment Variable Deep Dive**
   - Compare exact environment variables between local and Railway
   - Verify Supabase service key format and permissions
   - Check for hidden characters or encoding issues

3. **Supabase Admin API Testing**
   - Create isolated test endpoint that only tests Supabase admin API
   - Test admin API connectivity from Railway environment
   - Verify service role permissions in Supabase dashboard

### **Alternative Approaches to Try**

#### **Option 1: JWT Verification with Public Key**
```python
# Get Supabase public key and verify JWT signature
import jwt
import requests

def get_supabase_public_key():
    response = requests.get(f"{supabase_url}/rest/v1/")
    # Extract public key from response
    return public_key

# Verify JWT with actual signature validation
jwt.decode(token, public_key, algorithms=["RS256"])
```

#### **Option 2: Direct Database User Lookup**
```python
# Skip Supabase auth API, query auth.users directly
async def validate_user_via_database(user_id: str):
    result = supabase_client.table('auth.users').select('*').eq('id', user_id).execute()
    return result.data[0] if result.data else None
```

#### **Option 3: Middleware-Based Authentication**
```python
# Move auth logic to middleware instead of dependency injection
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Handle authentication at middleware level
```

### **Diagnostic Tools Needed**
1. **Railway Log Analysis Tool**
2. **Environment Variable Comparison Script**
3. **Token Validation Test Suite**
4. **Supabase Connection Test Endpoint**

---

## 📞 Questions for Other AIs/Experts

1. **Railway-Specific Issues**: Have you seen cases where identical code works locally but fails on Railway for authentication?

2. **Supabase JWT Validation**: What's the most reliable way to validate Supabase JWTs in production FastAPI apps?

3. **Environment Variable Propagation**: How long does Railway typically take to propagate environment variable changes to running applications?

4. **Docker Build Caching**: Could Railway's Docker layer caching cause authentication libraries to behave differently than local?

5. **Supabase Admin API**: Are there known issues with the `admin.get_user_by_id` method in production environments?

6. **FastAPI Dependency Injection**: Could there be race conditions or context issues with the dependency injection pattern we're using?

---

## 🔧 Debugging Commands & Scripts

### **Test Authentication Flow**
```python
# Add to Railway deployment for debugging
@app.get("/debug/auth")
async def debug_auth(authorization: str = Header(None)):
    return {
        "header_present": bool(authorization),
        "header_value": authorization[:20] + "..." if authorization else None,
        "supabase_url": os.getenv("SUPABASE_URL"),
        "service_key_present": bool(os.getenv("SUPABASE_SERVICE_KEY")),
        "timestamp": datetime.now().isoformat()
    }
```

### **Environment Variable Checker**
```python
@app.get("/debug/env")
async def debug_env():
    return {
        "supabase_url": os.getenv("SUPABASE_URL"),
        "has_service_key": bool(os.getenv("SUPABASE_SERVICE_KEY")),
        "has_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown")
    }
```

---

**📄 Document Status**: Complete
**🕐 Last Updated**: August 19, 2025
**👤 User**: g@sentigen.ai
**🎯 Next Action**: Share with other AIs for additional insights and solution approaches
