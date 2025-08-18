# Vercel Environment Variables Setup

## Required Environment Variables for Frontend

You need to add these environment variables in your Vercel project settings:

### 1. Go to Vercel Dashboard
- Navigate to your project: https://vercel.com/dashboard
- Click on your `Sentigen-Social` project
- Go to "Settings" → "Environment Variables"

### 2. Add These Variables

```bash
# Supabase Configuration (Required)
NEXT_PUBLIC_SUPABASE_URL=https://lvgrswaemwvmjdawsvdj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx2Z3Jzd2FlbXd2bWpkYXdzdmRqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjc2ODIsImV4cCI6MjA3MDk0MzY4Mn0.K9UEcOosRKzJitpe0gz9EXyaIPfyvHI71YTL90hjp9E

# API Configuration (Required)
NEXT_PUBLIC_API_URL=https://sentigen-social-production.up.railway.app

# App Configuration (Optional but recommended)
NEXT_PUBLIC_APP_NAME=zyyn
NEXT_PUBLIC_APP_DESCRIPTION=create at the speed of thought

# Feature Flags (Optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_AI_GENERATION=true
NEXT_PUBLIC_ENABLE_SCHEDULING=true
```

### 3. Apply to All Environments
Make sure to add these variables for:
- Production
- Preview
- Development

### 4. Redeploy
After adding the environment variables:
1. Go to "Deployments" tab
2. Click on the latest deployment
3. Click "Redeploy" → "Redeploy with existing Build Cache"

## Verification

Once deployed, your app should:
1. Show the login page at `/auth/login`
2. Allow users to sign in with email/password
3. Display the user's profile avatar (G) in the top-right when logged in
4. Allow access to the Pipeline and other authenticated features

## Troubleshooting

If you see errors after deployment:
1. Check the Vercel Function logs for any API errors
2. Verify all environment variables are set correctly
3. Make sure the Railway backend is running and accessible
4. Check browser console for any client-side errors

## Important Notes

- The `NEXT_PUBLIC_` prefix is required for client-side variables
- These variables are embedded at build time
- Changes to environment variables require a redeploy
- Never commit these values to your repository
