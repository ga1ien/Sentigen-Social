#!/usr/bin/env python3
"""
Complete Authentication Fix Guide

This script provides a step-by-step guide to fix authentication issues
between the Next.js frontend and FastAPI backend in Sentigen Social.

The main issue: JWT_SECRET environment variable is not set in Railway,
causing the backend to reject authenticated requests from the frontend.
"""

import os
import subprocess
import sys
from typing import List, Tuple


class AuthenticationFixer:
    """Guide for fixing authentication issues."""

    def __init__(self):
        self.steps_completed = []
        self.project_root = "/Users/galenoakes/Development/Sentigen-Social"

    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(f"🔧 {title}")
        print("=" * 60)

    def print_step(self, step_num: int, title: str, description: str = ""):
        """Print a formatted step."""
        print(f"\n📋 Step {step_num}: {title}")
        if description:
            print(f"   {description}")
        print("-" * 40)

    def print_success(self, message: str):
        """Print success message."""
        print(f"✅ {message}")

    def print_warning(self, message: str):
        """Print warning message."""
        print(f"⚠️ {message}")

    def print_error(self, message: str):
        """Print error message."""
        print(f"❌ {message}")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        self.print_header("Checking Prerequisites")

        # Check if we're in the right directory
        if not os.path.exists(os.path.join(self.project_root, "railway.toml")):
            self.print_error("Not in Sentigen Social project directory")
            return False

        self.print_success("In correct project directory")

        # Check if Railway CLI is available
        try:
            subprocess.run(["railway", "--version"], capture_output=True, check=True)
            self.print_success("Railway CLI is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_warning("Railway CLI not found - will need to install it")

        # Check if Python dependencies are available
        try:
            import requests
            self.print_success("Python requests library available")
        except ImportError:
            self.print_warning("Python requests library not found - install with: pip install requests")

        return True

    def explain_problem(self):
        """Explain the authentication problem."""
        self.print_header("Problem Diagnosis")

        print("""
🔍 PROBLEM IDENTIFIED:
The FastAPI backend is not recognizing authenticated users from the frontend.

📊 SYMPTOMS:
- User successfully logs in on frontend (profile picture shows)
- User clicks "Start Research" in pipeline
- Backend returns "401 Unauthorized" or "sign in required"
- FastAPI app appears to disconnect/reject the request

🔎 ROOT CAUSE:
The JWT_SECRET environment variable is not set in Railway deployment.
This causes the backend to fail when validating JWT tokens from the frontend.

💡 SOLUTION:
Set the JWT_SECRET to the Supabase Legacy JWT Secret in Railway environment.

🔧 TECHNICAL DETAILS:
- Frontend: Uses Supabase auth, stores JWT in localStorage
- Frontend: Axios interceptor adds "Bearer <token>" to API requests
- Backend: Tries to decode JWT using JWT_SECRET environment variable
- Backend: Falls back to Supabase validation if JWT decode fails
- Issue: JWT_SECRET not set → decode fails → auth fails
        """)

    def step_1_railway_setup(self):
        """Step 1: Set up Railway environment variables."""
        self.print_step(1, "Configure Railway Environment Variables",
                       "Set the missing JWT_SECRET and verify other variables")

        print("""
🎯 CRITICAL: The JWT_SECRET variable is missing from Railway!

📝 REQUIRED VARIABLES:
- JWT_SECRET: AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg==
- SUPABASE_URL: https://lvgrswaemwvmjdawsvdj.supabase.co
- SUPABASE_SERVICE_KEY: (get from Supabase dashboard)
- SUPABASE_ANON_KEY: (get from Supabase dashboard)

🚀 QUICK FIX:
Run the automated setup script:
        """)

        print(f"   cd {self.project_root}")
        print("   ./scripts/fix_railway_auth.sh")

        print("""
🔧 MANUAL FIX:
1. Go to https://railway.app
2. Select your 'sentigen-social-production' project
3. Click on the backend service
4. Go to "Variables" tab
5. Add JWT_SECRET with the value above
6. Add other Supabase variables
7. Deploy the changes

📖 DETAILED GUIDE:
See: railway_env_setup.md for complete instructions
        """)

        response = input("\n✋ Have you set the Railway environment variables? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            self.steps_completed.append(1)
            self.print_success("Railway environment variables configured")
            return True
        else:
            self.print_warning("Please configure Railway variables before continuing")
            return False

    def step_2_test_deployment(self):
        """Step 2: Test the Railway deployment."""
        self.print_step(2, "Test Railway Deployment",
                       "Verify the backend is running with correct configuration")

        print("""
🧪 TESTING OPTIONS:

Option A - Automated Test:
   cd {}/scripts
   python test_auth_flow.py auto

Option B - Manual Test:
   curl https://sentigen-social-production.up.railway.app/health

Option C - Check Railway Logs:
   railway logs --follow

Look for these log messages:
✅ "JWT_SECRET loaded from environment: AMo8kf6..."
❌ "JWT_SECRET not set in environment, using default (will fail)"
        """.format(self.project_root))

        response = input("\n✋ Does the health endpoint work and show JWT_SECRET loaded? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            self.steps_completed.append(2)
            self.print_success("Backend deployment verified")
            return True
        else:
            self.print_warning("Backend deployment needs attention")
            return False

    def step_3_test_jwt_validation(self):
        """Step 3: Test JWT token validation."""
        self.print_step(3, "Test JWT Token Validation",
                       "Verify the backend can validate frontend tokens")

        print(f"""
🎫 JWT VALIDATION TEST:

1. Local Test:
   cd {self.project_root}/social-media-module/backend
   export JWT_SECRET='AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg=='
   python test_jwt_validation.py

2. Follow the interactive prompts to test with a real token from the browser

3. You should see:
   ✅ Token validation successful!
   User ID: [your-user-id]
   Email: [your-email]
        """)

        response = input("\n✋ Does JWT validation work locally? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            self.steps_completed.append(3)
            self.print_success("JWT validation verified")
            return True
        else:
            self.print_warning("JWT validation needs attention")
            return False

    def step_4_test_full_flow(self):
        """Step 4: Test the complete authentication flow."""
        self.print_step(4, "Test Complete Authentication Flow",
                       "Test from frontend through to backend")

        print("""
🌐 FULL FLOW TEST:

1. Open https://zyyn.ai in your browser
2. Log in with your credentials
3. Go to Dashboard → Create → Pipeline
4. Enter a topic (e.g., "AI automation tools")
5. Select source (e.g., "Reddit")
6. Click "Start Research"

Expected Results:
✅ Research starts successfully
✅ Shows "Research running..."
✅ No "sign in required" errors
✅ Research completes and moves to next step

Alternative Test:
   cd scripts
   python test_auth_flow.py
   (Follow interactive prompts with browser token)
        """)

        response = input("\n✋ Does the research pipeline work without auth errors? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            self.steps_completed.append(4)
            self.print_success("Complete authentication flow verified")
            return True
        else:
            self.print_warning("Authentication flow still has issues")
            return False

    def troubleshooting_guide(self):
        """Provide troubleshooting guide."""
        self.print_header("Troubleshooting Guide")

        print("""
🔧 COMMON ISSUES & SOLUTIONS:

1. "sign in required" error:
   → JWT_SECRET not set in Railway
   → Run: railway variables set JWT_SECRET="AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg=="

2. "JWT decode error" in logs:
   → Wrong JWT_SECRET value
   → Check Supabase Dashboard → Settings → API → JWT Settings → Legacy JWT Secret

3. Health endpoint returns 500:
   → Missing SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
   → Set these in Railway variables

4. CORS errors in browser:
   → Set CORS_ORIGINS="https://zyyn.ai,https://www.zyyn.ai"

5. Token expires immediately:
   → Check Supabase auth settings
   → Verify frontend is using correct Supabase URL/keys

📋 DEBUG CHECKLIST:
□ JWT_SECRET set in Railway (most common issue)
□ SUPABASE_SERVICE_KEY set in Railway
□ SUPABASE_ANON_KEY set in Railway
□ Frontend and backend using same Supabase project
□ Railway service deployed successfully
□ Health endpoint returns 200 with JWT_SECRET loaded message
        """)

    def summary_and_next_steps(self):
        """Provide summary and next steps."""
        self.print_header("Summary & Next Steps")

        completed_count = len(self.steps_completed)
        total_steps = 4

        print(f"""
📊 PROGRESS: {completed_count}/{total_steps} steps completed

✅ Completed Steps: {self.steps_completed if self.steps_completed else 'None'}

🎯 NEXT ACTIONS:
        """)

        if completed_count == total_steps:
            print("""
🎉 ALL STEPS COMPLETED!
Your authentication should now be working properly.

🚀 PRODUCTION READY:
- Users can log in on frontend
- Backend recognizes authenticated users
- Research pipeline works without auth errors
- All API endpoints accessible to authenticated users

📈 MONITOR:
- Check Railway logs for any auth errors
- Monitor user reports of auth issues
- Verify other protected endpoints work

🔄 MAINTENANCE:
- JWT tokens expire - this is normal
- Frontend auto-refreshes tokens
- Monitor Supabase auth metrics
            """)
        else:
            missing_steps = [i for i in range(1, total_steps + 1) if i not in self.steps_completed]
            print(f"""
⏭️ REMAINING STEPS: {missing_steps}

🔧 IMMEDIATE PRIORITY:
1. Configure Railway environment variables (Step 1)
2. Deploy and verify backend (Step 2)
3. Test JWT validation (Step 3)
4. Test complete flow (Step 4)

💡 MOST LIKELY FIX:
The JWT_SECRET environment variable needs to be set in Railway.
This single fix should resolve the authentication issues.
            """)

        print("""
📚 HELPFUL FILES:
- railway_env_setup.md: Complete environment setup guide
- scripts/fix_railway_auth.sh: Automated Railway setup
- scripts/test_auth_flow.py: Test authentication flow
- social-media-module/backend/test_jwt_validation.py: Test JWT validation

🆘 GET HELP:
If issues persist, check:
1. Railway deployment logs
2. Browser network requests (look for 401 responses)
3. Supabase auth logs in dashboard
        """)

    def run_interactive_guide(self):
        """Run the complete interactive guide."""
        self.print_header("Sentigen Social Authentication Fix")

        print("""
🎯 GOAL: Fix authentication between Next.js frontend and FastAPI backend
📋 TIME: ~10-15 minutes
🔧 DIFFICULTY: Easy (mostly environment configuration)
        """)

        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please resolve and run again.")
            return False

        self.explain_problem()

        # Run through steps
        if not self.step_1_railway_setup():
            self.troubleshooting_guide()
            return False

        if not self.step_2_test_deployment():
            self.troubleshooting_guide()
            return False

        if not self.step_3_test_jwt_validation():
            self.troubleshooting_guide()
            return False

        if not self.step_4_test_full_flow():
            self.troubleshooting_guide()
            return False

        self.summary_and_next_steps()
        return True


def main():
    """Main function."""
    fixer = AuthenticationFixer()

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick mode - just show the most likely fix
        print("🚀 QUICK FIX for Authentication Issues:")
        print("="*50)
        print("\n🎯 Most likely cause: JWT_SECRET not set in Railway")
        print("\n💡 Quick fix:")
        print("1. Run: ./scripts/fix_railway_auth.sh")
        print("2. Test: curl https://sentigen-social-production.up.railway.app/health")
        print("3. Look for: 'JWT_SECRET loaded from environment' in logs")
        print("\n📖 Full guide: python fix_authentication.py")
    else:
        # Interactive mode
        success = fixer.run_interactive_guide()
        if success:
            print("\n🎉 Authentication fix completed successfully!")
        else:
            print("\n⚠️ Authentication fix needs attention. See troubleshooting above.")


if __name__ == "__main__":
    main()
