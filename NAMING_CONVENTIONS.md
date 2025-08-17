# 🐍 Naming Conventions Guide

This document outlines the strict naming conventions for the Sentigen Social platform to ensure consistency across the entire codebase.

## 📋 **Core Principle: snake_case for Data**

**All data-related fields, database columns, and API parameters MUST use snake_case.**

## 🎯 **Rules by Context**

### 🗄️ **Database (PostgreSQL)**
- **Tables**: `snake_case` (e.g., `user_social_accounts`, `avatar_profiles`)
- **Columns**: `snake_case` (e.g., `created_at`, `user_id`, `avatar_id`)
- **Indexes**: `snake_case` (e.g., `idx_users_email`, `idx_posts_workspace_id`)
- **Functions**: `snake_case` (e.g., `add_column_if_not_exists`)

```sql
-- ✅ CORRECT
CREATE TABLE user_social_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    platform_id UUID NOT NULL,
    account_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ❌ WRONG
CREATE TABLE userSocialAccounts (
    id UUID PRIMARY KEY,
    userId UUID NOT NULL,
    platformId UUID NOT NULL,
    accountName TEXT,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 🐍 **Python Backend**
- **Variables**: `snake_case` (e.g., `user_id`, `avatar_profile`, `video_generation`)
- **Functions**: `snake_case` (e.g., `get_user_videos`, `create_avatar_profile`)
- **Pydantic Fields**: `snake_case` (e.g., `media_urls`, `schedule_date`)
- **NO Field Aliases**: Removed all camelCase aliases
- **Classes**: `PascalCase` (e.g., `AvatarProfile`, `VideoGeneration`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_VIDEO_DURATION`, `DEFAULT_AVATAR_ID`)

```python
# ✅ CORRECT
class AvatarProfile(BaseModel):
    avatar_id: str = Field(..., description="HeyGen avatar ID")
    voice_id: str = Field(..., description="HeyGen voice ID")
    display_order: int = Field(default=0)
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

async def get_user_videos(user_id: str, workspace_id: str) -> List[VideoGeneration]:
    """Get user's video generations."""
    pass

# ❌ WRONG
class AvatarProfile(BaseModel):
    avatarId: str = Field(alias="avatarId")  # NO camelCase aliases!
    voiceId: str = Field(alias="voiceId")
    displayOrder: int = Field(alias="displayOrder")
    isDefault: bool = Field(alias="isDefault")
    createdAt: datetime = Field(alias="createdAt")

async def getUserVideos(userId: str, workspaceId: str) -> List[VideoGeneration]:
    pass
```

### ⚛️ **Frontend TypeScript**
- **API Interface Properties**: `snake_case` (matches backend/database)
- **Component Props**: `camelCase` (React standard)
- **Variables/Functions**: `camelCase` (JavaScript standard)
- **Types/Interfaces**: `PascalCase` (TypeScript standard)
- **Constants**: `UPPER_CASE`

```typescript
// ✅ CORRECT - API Interface (matches backend)
interface AvatarProfile {
  id: number
  avatar_id: string        // snake_case for API data
  voice_id: string
  display_order: number
  is_default: boolean
  created_at: string
}

// ✅ CORRECT - Component Props (React standard)
interface AvatarCardProps {
  avatarProfile: AvatarProfile  // camelCase for component props
  onSelect: (id: number) => void
  isSelected: boolean
}

// ✅ CORRECT - Component
function AvatarCard({ avatarProfile, onSelect, isSelected }: AvatarCardProps) {
  const handleClick = () => {    // camelCase for local variables
    onSelect(avatarProfile.id)
  }

  return (
    <div onClick={handleClick}>
      <h3>{avatarProfile.avatar_id}</h3>  {/* snake_case for API data */}
      <p>Order: {avatarProfile.display_order}</p>
    </div>
  )
}

// ❌ WRONG - Mixing conventions
interface AvatarProfile {
  avatarId: string     // Should be avatar_id to match backend
  voiceId: string      // Should be voice_id
  displayOrder: number // Should be display_order
}
```

### 🌐 **API Endpoints**
- **URL Paths**: `kebab-case` (e.g., `/api/avatar-profiles`, `/api/user-videos`)
- **Query Parameters**: `snake_case` (e.g., `?user_id=123&workspace_id=456`)
- **Request/Response Bodies**: `snake_case` (matches database)

```python
# ✅ CORRECT
@app.get("/api/avatar-profiles")
async def get_avatar_profiles(
    workspace_id: str,           # snake_case parameters
    avatar_type: Optional[str] = None
):
    return {"avatar_profiles": [...]}  # snake_case response

# ❌ WRONG
@app.get("/api/avatarProfiles")
async def getAvatarProfiles(
    workspaceId: str,            # Should be workspace_id
    avatarType: Optional[str] = None
):
    return {"avatarProfiles": [...]}  # Should be avatar_profiles
```

## 🔧 **Enforcement Tools**

### **Automated Validation**
- **Python**: `flake8`, `pylint`, `black`, `isort`
- **TypeScript**: `ESLint` with custom naming rules
- **Pre-commit Hooks**: Validate before every commit
- **Custom Script**: `scripts/validate_snake_case.py`

### **IDE Configuration**
Configure your IDE to highlight naming violations:

```json
// VS Code settings.json
{
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": true,
  "eslint.validate": ["typescript", "typescriptreact"],
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

## 🚫 **Common Mistakes to Avoid**

### **1. Mixing Conventions**
```python
# ❌ WRONG
class UserProfile(BaseModel):
    user_id: str = Field(alias="userId")  # Mixed snake_case field with camelCase alias
    firstName: str                        # camelCase field name
    last_name: str                        # Inconsistent with firstName
```

### **2. Frontend API Mismatches**
```typescript
// ❌ WRONG - Frontend doesn't match backend
interface User {
  userId: string      // Backend uses user_id
  firstName: string   // Backend uses first_name
  createdAt: string   // Backend uses created_at
}

// ✅ CORRECT - Frontend matches backend
interface User {
  user_id: string     // Matches backend exactly
  first_name: string  // Matches backend exactly
  created_at: string  // Matches backend exactly
}
```

### **3. Database Schema Inconsistencies**
```sql
-- ❌ WRONG
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firstName TEXT,      -- Should be first_name
    lastName TEXT,       -- Should be last_name
    createdAt TIMESTAMP  -- Should be created_at
);
```

## ✅ **Validation Checklist**

Before committing code, ensure:

- [ ] All database columns use `snake_case`
- [ ] All Python variables/functions use `snake_case`
- [ ] All Pydantic fields use `snake_case` (no camelCase aliases)
- [ ] Frontend API interfaces use `snake_case` for data properties
- [ ] API endpoints use `snake_case` for parameters
- [ ] Pre-commit hooks pass without violations
- [ ] ESLint/Flake8 show no naming convention errors

## 🔄 **Migration Strategy**

When updating existing code:

1. **Database**: Use incremental migrations with column renames
2. **Backend**: Remove field aliases, update all references
3. **Frontend**: Update interface definitions to match backend
4. **API**: Maintain backward compatibility during transition
5. **Documentation**: Update all examples and guides

## 📞 **Questions?**

If you're unsure about a naming convention:
1. Check this guide first
2. Look at existing code in the same context
3. Run the validation script: `python scripts/validate_snake_case.py`
4. Ask the team for clarification

**Remember: Consistency is key! When in doubt, use snake_case for data. 🐍**
