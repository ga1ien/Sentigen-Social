# Authentication Setup Guide

## Overview
The authentication system is built using Supabase Auth and is integrated throughout the application. This guide will help you set up and configure authentication properly.

## Prerequisites
1. A Supabase project (create one at https://supabase.com)
2. Environment variables configured
3. Database schema applied

## Environment Configuration

### Frontend Configuration
Create a `.env.local` file in the `frontend/` directory with the following variables:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration
NEXT_PUBLIC_API_URL=https://sentigen-social-production.up.railway.app

# App Configuration
NEXT_PUBLIC_APP_NAME=zyyn
NEXT_PUBLIC_APP_DESCRIPTION=create at the speed of thought

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_AI_GENERATION=true
NEXT_PUBLIC_ENABLE_SCHEDULING=true
```

### Backend Configuration
Create a `.env` file in the `social-media-module/backend/` directory:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# JWT Configuration
JWT_SECRET=your_jwt_secret_key
```

## Supabase Setup

### 1. Enable Authentication Providers

1. Go to your Supabase project dashboard
2. Navigate to Authentication → Providers
3. Enable the following providers:
   - **Email/Password**: Enable for basic authentication
   - **GitHub**: For OAuth login (optional but recommended)
     - Add your GitHub OAuth App credentials
     - Set callback URL to: `https://your-domain.com/auth/callback`

### 2. Configure Auth Settings

1. Go to Authentication → Settings
2. Configure the following:
   - **Site URL**: `https://your-domain.com` (or `http://localhost:3000` for development)
   - **Redirect URLs**: Add the following URLs:
     - `http://localhost:3000/auth/callback`
     - `https://your-domain.com/auth/callback`
     - `http://localhost:3000/dashboard`
     - `https://your-domain.com/dashboard`

### 3. User Metadata

The application expects the following user metadata fields:
- `full_name`: User's display name
- `avatar_url` or `picture`: URL to user's profile picture
- `subscription_tier`: User's subscription level (defaults to "free")

These are automatically populated for OAuth providers like GitHub.

## Features

### Current Implementation

1. **User Profile Avatar**:
   - Displays user's profile picture in the top-right corner
   - Falls back to initials if no picture is available
   - Beautiful gradient background for fallback avatar

2. **Authentication Flow**:
   - Email/Password registration and login
   - GitHub OAuth integration
   - Email verification for new accounts
   - Password reset functionality
   - Secure session management

3. **User Context**:
   - Global user state management
   - Automatic session refresh
   - Loading states during authentication
   - Proper error handling

4. **Protected Routes**:
   - Dashboard routes require authentication
   - Automatic redirection for unauthenticated users
   - Auth pages redirect to dashboard if already logged in

## Testing Authentication

### 1. Local Development

```bash
# Start the frontend
cd frontend
npm install
npm run dev

# Start the backend (in another terminal)
cd social-media-module/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python api/main.py
```

### 2. Test Registration
1. Navigate to `http://localhost:3000/auth/register`
2. Fill in the registration form
3. Check your email for verification link
4. Click the verification link
5. You should be redirected to the dashboard

### 3. Test Login
1. Navigate to `http://localhost:3000/auth/login`
2. Enter your credentials
3. You should be redirected to the dashboard
4. Your profile picture/initial should appear in the top-right

### 4. Test GitHub OAuth
1. Click "Continue with GitHub" on login/register page
2. Authorize the application
3. You should be redirected to the dashboard
4. Your GitHub profile picture should appear in the top-right

## Troubleshooting

### Common Issues

1. **"Supabase not configured" error**
   - Ensure environment variables are set correctly
   - Check that `.env.local` file exists in frontend directory
   - Restart the development server after adding environment variables

2. **Profile picture not showing**
   - Check if `user_metadata` contains `avatar_url` or `picture`
   - For GitHub OAuth, ensure profile picture is public
   - Check browser console for image loading errors

3. **Authentication not persisting**
   - Check Supabase dashboard for active sessions
   - Ensure cookies are enabled in browser
   - Check middleware configuration in `frontend/src/middleware.ts`

4. **Redirect issues after login**
   - Verify redirect URLs in Supabase dashboard
   - Check `auth/callback` page implementation
   - Ensure middleware is not blocking authenticated routes

## API Endpoints

The backend provides the following authentication endpoints:

- `GET /api/user/me` - Get current user information
- `POST /api/auth/verify` - Verify JWT token
- `GET /api/health` - Check API health and auth status

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Service Keys**: Keep service role keys secure and only use in backend
3. **CORS**: Configure appropriate CORS settings for production
4. **HTTPS**: Always use HTTPS in production
5. **Session Management**: Implement proper session timeout and refresh

## Next Steps

1. Configure email templates in Supabase for better branding
2. Add more OAuth providers (Google, Twitter, etc.)
3. Implement role-based access control (RBAC)
4. Add two-factor authentication (2FA)
5. Set up user profile management page
