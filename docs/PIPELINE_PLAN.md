## zyyn v1 Research-to-Content Pipeline

Goal: A single, intentional flow that feels magical:
- Research a topic → synthesize content (Script or LinkedIn Post) → edit → save → post now / schedule (or create video with HeyGen, then post/schedule to shorts).

### Providers
- Writing: Claude 4 Sonnet (Anthropic)
- Tool calls/normalization: GPT‑5 Mini
- Social posting: Ayrshare (Post + Auto Schedule)
- Video: HeyGen (create/poll)

### Backend Endpoints (existing + small additions)
1) Research
   - Start: POST `/api/research/start` { query, source: reddit|hackernews|github|google_trends, max_items, analysis_depth }
   - List sessions: GET `/api/research/sessions`
   - Session detail: GET `/api/research/sessions/{id}`
   - Generate from research: POST `/api/research/generate-content` { research_session_id, content_type: post|article|thread|summary, platform, tone, length }

2) Content drafting and saving
   - Draft save: `content_drafts` table insert (used already in content_research_api). Ensure table exists in schema.

3) Posting & Scheduling (Ayrshare)
   - Immediate: POST `/api/social-posting/create` { content, platforms, media_urls? }
   - Schedule exact time: same endpoint + `schedule_date` (maps to Ayrshare `scheduleDate`)
   - Auto Schedule queue: same endpoint + `auto_schedule: { schedule: true, title?: 'default' }` (maps to Ayrshare `autoSchedule`). Use either `autoSchedule` or `scheduleDate`.
   - References: Ayrshare Quick Start + Auto Schedule
     - https://www.ayrshare.com/docs/quickstart
     - https://www.ayrshare.com/docs/apis/auto-schedule/overview

4) HeyGen Video
   - Create script video: POST `/api/heygen/video` { script, avatar_id?, voice_id? }
   - Poll: GET `/api/heygen/video/{video_id}` → when ready, return playable URL/asset
   - Then schedule/post shorts via `/api/social-posting/create` for platforms in [tiktok, youtube, instagram]
   - Reference: https://docs.heygen.com/docs/create-video

### Frontend Flow (Dashboard → Create)
Step 1: Choose Output
- Two large glass buttons: "Script" or "LinkedIn post"

Step 2: Topic & Research
- Input topic → click "Research" → POST `/api/research/start`
- Show live status for the session. When completed, enable "Use research".

Step 3: Synthesize & Edit
- POST `/api/research/generate-content` with content_type based on selection (Script → article or summary; LinkedIn → post + platform="linkedin"). Claude 4 Sonnet used.
- Populate editable textarea; allow save to drafts.

Step 4A: Publish LinkedIn
- Buttons: "Post now", "Schedule (datetime)", "Auto Schedule".
- "Post now": POST `/api/social-posting/create` { content, platforms:["linkedin"] }
- "Schedule": same endpoint + `schedule_date`
- "Auto Schedule": same endpoint + `auto_schedule: { schedule: true, title: 'default' }`

Step 4B: Script → Video → Shorts
- "Create video (HeyGen)": POST `/api/heygen/video` then poll status.
- On ready: choose targets (tiktok, youtube, instagram), then Post now / Schedule / Auto Schedule via social-posting endpoint.

### Data Model Notes
- Ensure `content_drafts` exists (id, user_id, platform?, title?, content, status, created_at).
- `social_media_posts` used for storing post lifecycles (already present).

### Implementation Steps
1) Backend
   - Add `auto_schedule` passthrough to `/api/social-posting/create` to map to Ayrshare `autoSchedule`.
   - Verify HeyGen endpoints in `api/main.py` function as expected.
   - Ensure `content_drafts` migration exists (007 or later) and RLS policies.

2) Frontend
   - Refactor `/dashboard/create` into 4-step guided flow with glass UI.
   - Wire research start/list/session → generate-content → edit text → save draft → publish/schedule/auto.
   - Script branch: HeyGen create/poll UI + shorts scheduling.

### Guardrails
- Use either `autoSchedule` or `scheduleDate` per Ayrshare (not both).
- Keep UI minimal: large glass containers, dark text, ambient background.
- Primary: flow correctness and reliability; de-scope analytics/calendar for v1.
