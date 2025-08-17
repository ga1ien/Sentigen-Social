# 📊 Database Schema Analysis & Consolidation Plan

**Created**: December 2024
**Purpose**: Analyze differences between database schemas and plan consolidation

---

## 🔍 Schema Comparison Overview

### Schema A: `/database/complete_supabase_schema.sql`
- **Size**: ~500+ lines
- **Tables**: 20 tables
- **Features**: Comprehensive, includes all platform features
- **Namespace**: Uses `public.` prefix
- **Focus**: Production-ready with full feature set

### Schema B: `/social-media-module/backend/database/consolidated_schema.sql`
- **Size**: ~300+ lines
- **Tables**: 18 tables
- **Features**: Backend-focused, missing some features
- **Namespace**: No prefix (assumes public)
- **Focus**: Backend development with worker system

---

## 📋 Detailed Table Comparison

### ✅ Tables in BOTH Schemas
| Table Name | Schema A | Schema B | Status |
|------------|----------|----------|---------|
| `users` | ✅ | ✅ | **Different structure** |
| `workspaces` | ✅ | ✅ | **Different structure** |
| `social_media_posts` | ✅ | ✅ | **Different structure** |
| `avatar_profiles` | ✅ | ✅ | **Similar structure** |
| `script_generations` | ✅ | ✅ | **Similar structure** |
| `video_generations` | ✅ | ✅ | **Different structure** |
| `workflow_executions` | ✅ | ✅ | **Similar structure** |

### 🔴 Tables ONLY in Schema A (Complete)
| Table Name | Purpose | Critical? |
|------------|---------|-----------|
| `workspace_members` | Team collaboration | ✅ **YES** |
| `social_platforms` | Platform definitions | ✅ **YES** |
| `user_social_accounts` | Connected accounts | ✅ **YES** |
| `content_posts` | Content management | ✅ **YES** |
| `content_media` | Media attachments | ✅ **YES** |
| `post_publications` | Publishing tracking | ✅ **YES** |
| `video_analytics` | Video performance | 🟡 **NICE** |
| `user_video_limits` | Subscription limits | ✅ **YES** |
| `avatar_usage_stats` | Usage tracking | 🟡 **NICE** |
| `content_insights` | Research insights | ✅ **YES** |
| `content_recommendations` | AI recommendations | ✅ **YES** |
| `platform_analytics` | Social media metrics | ✅ **YES** |
| `user_activity_logs` | Audit trail | ✅ **YES** |

### 🟡 Tables ONLY in Schema B (Consolidated)
| Table Name | Purpose | Critical? |
|------------|---------|-----------|
| `media_assets` | File management | ✅ **YES** |
| `content_templates` | Content templates | 🟡 **NICE** |
| `worker_tasks` | Background jobs | ✅ **YES** |
| `worker_results` | Job results | ✅ **YES** |
| `research_configurations` | Research settings | ✅ **YES** |
| `research_jobs` | Research execution | ✅ **YES** |
| `research_results` | Research data | ✅ **YES** |
| `workflow_approvals` | Approval workflow | 🟡 **NICE** |
| `analytics_events` | Event tracking | ✅ **YES** |
| `content_embeddings` | Vector search | ✅ **YES** |

---

## 🚨 Critical Structural Differences

### 1. Users Table Structure
```sql
-- Schema A (Complete)
CREATE TABLE public.users (
    subscription_tier TEXT DEFAULT 'free' CHECK (...),
    is_admin BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}'
);

-- Schema B (Consolidated)
CREATE TABLE users (
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (...)
);
```
**Issue**: Different role/admin systems, different field types

### 2. Social Media Posts Structure
```sql
-- Schema A: Separate content_posts + social_media_posts
-- Schema B: Single social_media_posts table
```
**Issue**: Different content management approaches

### 3. Research System
```sql
-- Schema A: Basic content_insights + content_recommendations
-- Schema B: Full research_* tables (configurations, jobs, results)
```
**Issue**: Schema B has more comprehensive research system

---

## 🎯 Consolidation Strategy

### **Recommended Approach: Hybrid Schema**
**Combine the best of both schemas**

#### Phase 1: Use Schema A as Base
- ✅ More comprehensive feature coverage
- ✅ Production-ready RLS policies
- ✅ Proper indexes and triggers
- ✅ Complete social media management

#### Phase 2: Add Missing Tables from Schema B
- ✅ `worker_tasks` & `worker_results` (critical for background jobs)
- ✅ `research_configurations`, `research_jobs`, `research_results` (research system)
- ✅ `media_assets` (better than content_media)
- ✅ `content_embeddings` (vector search)
- ✅ `analytics_events` (event tracking)

#### Phase 3: Reconcile Structural Differences
- 🔧 Merge user role systems
- 🔧 Standardize content management
- 🔧 Align field types and constraints

---

## 📝 Implementation Plan

### Step 1: Create Unified Schema
```sql
-- Start with complete_supabase_schema.sql
-- Add missing tables from consolidated_schema.sql
-- Reconcile structural differences
-- Update all constraints and indexes
```

### Step 2: Update Code References
```python
# Update database/models.py
# Fix import paths in backend code
# Update migration scripts
# Test all database operations
```

### Step 3: Migration Strategy
```sql
-- Create migration script
-- Backup existing data
-- Apply unified schema
-- Migrate data between table structures
-- Validate all operations
```

---

## ⚠️ Risk Assessment

### High Risk Items
1. **Data Loss**: Different table structures may cause data loss
2. **Downtime**: Schema changes require maintenance window
3. **Code Breakage**: Model changes will break existing code
4. **RLS Policies**: Need to ensure security policies still work

### Mitigation Strategies
1. **Full Backup**: Before any changes
2. **Staging Test**: Test migration on copy of production data
3. **Incremental Rollout**: Apply changes in phases
4. **Rollback Plan**: Prepared rollback scripts

---

## 🎯 Next Actions

### Immediate (Today)
1. ✅ **Create unified schema file**
2. ✅ **Backup existing schemas**
3. ✅ **Update model definitions**

### This Week
1. 🔧 **Test unified schema**
2. 🔧 **Update all code references**
3. 🔧 **Create migration scripts**
4. 🔧 **Validate all operations**

### Success Criteria
- [ ] Single authoritative schema file
- [ ] All features working with unified schema
- [ ] No data loss during migration
- [ ] All tests passing
- [ ] Code references updated

---

**Recommendation**: Proceed with hybrid approach, using Schema A as base and adding critical tables from Schema B. This preserves the comprehensive feature set while adding the advanced research and worker systems.
