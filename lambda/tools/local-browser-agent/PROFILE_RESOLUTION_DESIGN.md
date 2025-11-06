# Profile Resolution Design: Capability-Based Matching

**Version**: 1.0
**Date**: 2025-11-06
**Status**: Implementation in Progress

## Executive Summary

This document describes the profile resolution system for the Local Browser Agent, which enables scalable mapping between cloud-defined automation requirements and locally-managed browser profiles across hundreds of users and machines.

**Core Principle**: The cloud specifies **what capabilities are needed** (via tags), not **which specific profile to use** (via names). Each client resolves the requirement to a local profile independently.

---

## Problem Statement

### The Challenge

In a large-scale deployment with hundreds of users:

1. **Namespace Collision**: Cloud can't dictate local profile names
   - User 1 names their Amazon profile: `"My_Amazon"`
   - User 2 names theirs: `"Personal_Shopping"`
   - Cloud needs to reference "an authenticated Amazon profile"

2. **Two Usage Modes**:
   - **Personal Mode**: User-specific work (e.g., "check MY Amazon orders")
   - **Pool Mode**: Generic work (e.g., "check product availability on ANY account")

3. **Scale Requirements**:
   - 100s of users with different local naming conventions
   - 100s of cloud agents (Step Functions activities)
   - 1000s of concurrent executions
   - No new infrastructure or communication channels

### Current State

**Today** (v0.1.x):
```json
// Cloud sends exact profile name
{
  "session": {
    "profile_name": "Bt_broadband"  // Hardcoded, not scalable
  }
}
```

**Problems**:
- Cloud must know each user's local profile names
- Doesn't work for pool mode (multiple clients)
- No fallback mechanism
- Tight coupling between cloud and client

---

## Solution: Capability-Based Tag Matching

### Core Concept

Instead of exact names, use **semantic tags** that describe profile capabilities:

```json
// Cloud sends capability requirements
{
  "session": {
    "required_tags": ["amazon.com", "authenticated"],
    "profile_name": "amazon_default",  // Optional hint
    "allow_temp_profile": false
  }
}

// Client resolves locally
// User 1: "My_Amazon" with tags ["amazon.com", "authenticated"] ✓
// User 2: "Personal_Shopping" with tags ["amazon.com", "authenticated"] ✓
// Pool machine: "Pool_Amazon_01" with tags ["amazon.com", "authenticated", "pool"] ✓
```

### Resolution Algorithm

**Priority order**:

1. **Exact name match** (if `profile_name` provided)
   - Backward compatible with existing scripts
   - Direct resolution when name is known

2. **Tag-based matching** (if `required_tags` provided)
   - Find any profile with ALL required tags
   - Use first match (or future: best match by last_used)

3. **Temporary profile** (if `allow_temp_profile: true`)
   - No persistent session
   - For unauthenticated workflows

4. **Error** (if nothing matches)
   - Return clear error to cloud
   - Activity task fails with actionable message

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cloud (Orchestrator)                  │
│                                                              │
│  Step Functions State Machine                                │
│    → Activity Task: {                                        │
│         "session": {                                         │
│           "required_tags": ["amazon.com", "authenticated"],  │
│           "allow_temp_profile": false                        │
│         },                                                   │
│         "steps": [...]                                       │
│       }                                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Step Functions Activity API
                           │ (existing - no changes)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Local Browser Agent (Client)                    │
│                                                              │
│  1. Activity Poller receives task                           │
│  2. Profile Resolver:                                        │
│     • Parse required_tags                                    │
│     • Query local profile_manager                           │
│     • Match by tags (OR exact name)                         │
│     • Return matched profile config                         │
│  3. NovaAct Executor:                                        │
│     • Load profile's user_data_dir                          │
│     • Launch browser with saved session                     │
│     • Execute automation steps                              │
│  4. Return results to cloud                                  │
└─────────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│  Local Profile Storage (~/.local-browser-agent/profiles/)   │
│                                                              │
│  profiles.json:                                             │
│  {                                                          │
│    "My_Amazon": {                                           │
│      "tags": ["amazon.com", "authenticated", "personal"],   │
│      "user_data_dir": "/path/to/amazon_profile",           │
│      "last_used": "2025-11-06T10:00:00Z"                   │
│    },                                                       │
│    "Pool_Amazon_01": {                                      │
│      "tags": ["amazon.com", "authenticated", "pool"],       │
│      "user_data_dir": "/path/to/pool_amazon",              │
│      "last_used": "2025-11-06T09:00:00Z"                   │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Properties

✅ **No new infrastructure**: Uses existing Step Functions Activity API
✅ **No new storage**: Uses existing profile_manager.py
✅ **No new network calls**: Resolution happens entirely on client
✅ **Backward compatible**: Exact `profile_name` still works
✅ **Secure**: Credentials never leave local machine

---

## Implementation Plan

### Phase 1: Core Profile Resolution (Current Release - v0.2.0)

**Files to modify**:

1. **`python/script_executor.py`** - Add tag-based resolution
   - New function: `resolve_profile_by_tags()`
   - Modify: `execute_script()` to use resolver
   - ~50 lines of code

2. **`python/nova_act_wrapper.py`** - Add tag-based resolution
   - New function: `resolve_profile_by_tags()`
   - Modify: `execute_browser_command()` to use resolver
   - ~50 lines of code

3. **`python/profile_manager.py`** - Enhance tag filtering
   - Add: `--match-all-tags` flag to `list` command
   - Current `list --tags` does OR matching, need AND matching
   - ~20 lines of code

**Testing**:
- Unit tests for tag resolution logic
- Integration test: Cloud sends tags, client resolves
- Test: Multiple profiles with overlapping tags
- Test: No matching profile (error handling)
- Test: Backward compatibility (exact name still works)

**Deliverables**:
- Tag-based resolution working end-to-end
- Backward compatible with existing exact name matching
- Error messages guide users on how to create needed profiles

### Phase 2: Enhanced Tag Support (v0.3.0)

**Profile UI enhancements**:

1. **`ui/src/components/ProfilesScreen.tsx`**
   - Visual tag selector/autocomplete
   - Common tags suggestion (amazon.com, google.com, etc.)
   - Tag validation (no spaces, lowercase)
   - Show which cloud activities can use this profile

2. **Cloud template examples**:
   - Update example scripts to use `required_tags`
   - Document tag taxonomy and best practices
   - Migration guide from exact names to tags

**Deliverables**:
- User-friendly tag creation UI
- Tag autocomplete with suggestions
- Documentation and examples

### Phase 3: Smart Matching (v0.4.0)

**Enhanced resolution logic**:

1. **Multiple matches**: If >1 profile matches tags
   - Strategy 1: Use most recently used (`last_used` timestamp)
   - Strategy 2: Round-robin for load balancing
   - Strategy 3: User preference (primary/backup profiles)

2. **Partial matches**: If no exact tag match
   - Find profiles with superset of tags
   - Warn user: "Using profile with extra capabilities"
   - Allow/deny in session config

3. **Profile health checking**:
   - Track session expiry (cookies expired?)
   - Mark profiles as `healthy`, `expired`, or `unknown`
   - Skip expired profiles during resolution

**Deliverables**:
- Intelligent multi-match resolution
- Profile health tracking
- Session expiry detection

---

## Tag Taxonomy

### Standard Tag Categories

#### 1. **Domain Tags** (required)
Identifies the website/service:
- `amazon.com`
- `google.com`
- `salesforce.com`
- `bt.com`
- `github.com`

#### 2. **Authentication Tags** (required)
Indicates session state:
- `authenticated` - Logged in, has cookies/tokens
- `unauthenticated` - No login required
- `mfa-enabled` - Has MFA configured

#### 3. **Purpose Tags** (optional)
Distinguishes usage mode:
- `personal` - User-specific work
- `pool` - Shared work queue
- `testing` - Test environment only
- `production` - Production environment only

#### 4. **Permission Tags** (optional)
Indicates account capabilities:
- `read-only` - Can only view data
- `buyer` - Can make purchases
- `admin` - Has admin privileges
- `api-access` - Has API keys configured

#### 5. **Custom Tags** (optional)
User/organization-specific:
- `team:sales`
- `region:us-east`
- `priority:high`

### Tag Naming Conventions

**Rules**:
1. Lowercase only: `amazon.com` not `Amazon.com`
2. No spaces: Use hyphens: `read-only` not `read only`
3. Use dots for domains: `amazon.com` not `amazon`
4. Use colons for namespaces: `team:sales`, `region:us`
5. Keep simple: `authenticated` not `is_authenticated`

**Examples**:
```python
# Good tags
["amazon.com", "authenticated", "buyer", "personal"]

# Bad tags
["Amazon.com", "is authenticated", "amazoncom", "MY PROFILE"]
```

---

## Usage Patterns

### Pattern 1: Personal Automation

**User creates profile**:
```bash
# User creates their personal Amazon profile
python profile_manager.py create \
  --profile "My_Amazon_Shopping" \
  --tags "amazon.com" "authenticated" "buyer" "personal" \
  --description "My personal Amazon account"

# User sets up login manually
python profile_manager.py setup-login \
  --profile "My_Amazon_Shopping" \
  --url "https://www.amazon.com"
```

**Cloud sends work**:
```json
{
  "session": {
    "required_tags": ["amazon.com", "authenticated", "buyer"],
    "allow_temp_profile": false
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Go to my orders and check if package #123 has shipped"
    }
  ]
}
```

**Resolution**:
- Client sees: `required_tags: ["amazon.com", "authenticated", "buyer"]`
- Matches: `"My_Amazon_Shopping"` (has all required tags)
- Uses: User's personal profile with saved login
- Result: Automation runs as the user

### Pattern 2: Shared Pool Workers

**Admin sets up pool machines**:
```bash
# On machine 1
python profile_manager.py create \
  --profile "Pool_Amazon_01" \
  --tags "amazon.com" "authenticated" "read-only" "pool" \
  --description "Pool worker for Amazon data extraction"

# On machine 2
python profile_manager.py create \
  --profile "Pool_Amazon_02" \
  --tags "amazon.com" "authenticated" "read-only" "pool" \
  --description "Pool worker for Amazon data extraction"
```

**Cloud sends generic work**:
```json
{
  "session": {
    "required_tags": ["amazon.com", "authenticated", "pool"],
    "allow_temp_profile": false
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Extract product details from search results"
    }
  ]
}
```

**Resolution**:
- Both machines can handle this (have all required tags)
- Self-organizing: Whichever polls first gets the work
- No coordination needed between machines
- Scales to 100s of pool workers

### Pattern 3: Mixed Mode (Personal + Pool)

**User has both types**:
```bash
# Personal profile (no "pool" tag)
python profile_manager.py create \
  --profile "Alice_Personal" \
  --tags "amazon.com" "authenticated" "buyer" "personal"

# Pool profile (has "pool" tag)
python profile_manager.py create \
  --profile "Alice_Pool_Worker" \
  --tags "amazon.com" "authenticated" "read-only" "pool"
```

**Cloud distinguishes**:
```json
// Personal work - only matches "Alice_Personal"
{
  "required_tags": ["amazon.com", "authenticated", "buyer"],
  // No "pool" tag required
}

// Pool work - only matches "Alice_Pool_Worker"
{
  "required_tags": ["amazon.com", "authenticated", "pool"],
  // Must have "pool" tag
}
```

**Result**: Same machine can do both personal and pool work, correctly isolated by tags.

---

## Security Considerations

### 1. **Credentials Never Leave Local Machine**

- Profile data stays in `~/.local-browser-agent/`
- Cloud only sees tags, never actual profile names
- Passwords/cookies stored locally only
- No central registry of user credentials

### 2. **Tag-Based Access Control**

```json
// Restrict to read-only profiles only
{
  "required_tags": ["salesforce.com", "authenticated", "read-only"]
}
```

- Cloud can require `read-only` tag for safe operations
- User controls which profiles have which tags
- Prevents accidental use of admin accounts for bulk operations

### 3. **Profile Isolation**

```python
# Personal profiles won't match pool work
personal_tags = ["amazon.com", "authenticated", "personal"]
pool_requirement = ["amazon.com", "authenticated", "pool"]
# No match - "pool" tag not in personal_tags
```

- Users can keep personal profiles separate
- Admin can enforce `pool` tag for shared machines
- No accidental mixing of personal/pool work

### 4. **Audit Trail**

```python
# Log every profile resolution
log.info(
    f"Resolved profile: '{profile_name}' "
    f"for tags: {required_tags} "
    f"at: {timestamp}"
)
```

- Track which profile was used for each activity
- Detect unusual access patterns
- Compliance and debugging

---

## Error Handling

### Scenario 1: No Matching Profile

**Cloud request**:
```json
{
  "required_tags": ["salesforce.com", "authenticated", "admin"]
}
```

**Client response**:
```json
{
  "success": false,
  "error": "No suitable profile found",
  "error_type": "ProfileNotFoundError",
  "details": {
    "required_tags": ["salesforce.com", "authenticated", "admin"],
    "available_profiles": [
      {
        "name": "My_Salesforce",
        "tags": ["salesforce.com", "authenticated", "read-only"],
        "missing_tags": ["admin"]
      }
    ],
    "suggestion": "Create a profile with tags: [salesforce.com, authenticated, admin]"
  }
}
```

**User action**: Create the needed profile or update existing profile's tags.

### Scenario 2: Profile Session Expired

**Resolution result**:
```json
{
  "success": false,
  "error": "Profile session expired",
  "error_type": "SessionExpiredError",
  "details": {
    "profile_name": "My_Amazon",
    "last_used": "2024-10-01T10:00:00Z",
    "suggestion": "Run 'setup-login' to re-authenticate this profile"
  }
}
```

**User action**: Re-run manual login setup for the profile.

### Scenario 3: Multiple Matches (Future Enhancement)

**Resolution result**:
```python
# Multiple profiles match
matched_profiles = [
    {"name": "Amazon_Personal", "last_used": "2025-11-06T09:00:00Z"},
    {"name": "Amazon_Work", "last_used": "2025-11-05T14:00:00Z"},
]

# Strategy: Use most recently used
selected_profile = matched_profiles[0]  # Amazon_Personal

log.info(
    f"Multiple profiles matched tags {required_tags}. "
    f"Selected '{selected_profile['name']}' (most recently used)"
)
```

---

## Migration Guide

### For Existing Scripts (v0.1.x → v0.2.0)

**Before** (exact name only):
```json
{
  "session": {
    "profile_name": "Bt_broadband"
  }
}
```

**After** (hybrid - backward compatible):
```json
{
  "session": {
    "profile_name": "Bt_broadband",  // Try exact match first
    "required_tags": ["bt.com", "authenticated"],  // Fallback to tags
    "allow_temp_profile": false
  }
}
```

**Future** (tag-based only):
```json
{
  "session": {
    "required_tags": ["bt.com", "authenticated"],
    "allow_temp_profile": false
  }
}
```

### For Users

**Step 1**: Add tags to existing profiles
```bash
# Update existing profile with tags
python profile_manager.py update \
  --profile "Bt_broadband" \
  --add-tags "bt.com" "authenticated" "personal"
```

**Step 2**: Test with new scripts that use tags

**Step 3**: Remove `profile_name` from cloud templates once all clients upgraded

---

## Performance Considerations

### Tag Matching Performance

**Current implementation**:
- Profile count: Typically <50 per client
- Tag matching: O(n * m) where n=profiles, m=tags per profile
- Time complexity: ~1ms for 50 profiles with 5 tags each
- **Conclusion**: No optimization needed for expected scale

**Future optimization** (if >1000 profiles per client):
- Build inverted index: `tag → [profile_ids]`
- Intersection of tag sets for O(k * log(n)) where k=required tags
- Cache tag index, rebuild on profile changes

### Cloud Impact

**No additional load**:
- Resolution happens on client only
- Step Functions Activity API unchanged
- Same payload size (tags ≈ names in bytes)
- Same polling frequency

---

## Testing Strategy

### Unit Tests

1. **Profile resolution logic**:
   ```python
   def test_exact_name_match():
       # Given: profile exists with exact name
       # When: resolve with profile_name
       # Then: returns that profile

   def test_tag_match_single():
       # Given: profile with tags [A, B, C]
       # When: resolve with required_tags [A, B]
       # Then: returns that profile

   def test_tag_match_multiple():
       # Given: 2 profiles with tags [A, B]
       # When: resolve with required_tags [A, B]
       # Then: returns first match (or most recent)

   def test_no_match_error():
       # Given: no profiles match
       # When: resolve with required_tags [X, Y]
       # Then: raises ProfileNotFoundError with helpful message

   def test_temp_profile_fallback():
       # Given: no profiles match, allow_temp_profile=true
       # When: resolve
       # Then: returns None (temp profile)
   ```

2. **Tag filtering in profile_manager.py**:
   ```python
   def test_list_profiles_all_tags():
       # Given: profiles with various tags
       # When: list --tags "A" "B" --match-all
       # Then: returns only profiles with BOTH A and B
   ```

### Integration Tests

1. **End-to-end tag resolution**:
   ```python
   def test_activity_with_tags():
       # Given: client with profile tagged [amazon.com, authenticated]
       # When: activity task with required_tags [amazon.com, authenticated]
       # Then: profile resolved, browser opens, script executes
   ```

2. **Backward compatibility**:
   ```python
   def test_exact_name_still_works():
       # Given: old script with profile_name only
       # When: activity task with profile_name "My_Profile"
       # Then: resolves by exact name, works as before
   ```

3. **Error handling**:
   ```python
   def test_no_profile_returns_error():
       # Given: no matching profiles
       # When: activity task requires tags
       # Then: task fails with helpful error message
   ```

---

## Monitoring and Observability

### Metrics to Track

1. **Profile resolution success rate**:
   - Total resolutions attempted
   - Successful exact name matches
   - Successful tag matches
   - Failed resolutions (no match)

2. **Profile usage distribution**:
   - Which profiles are used most often
   - Which tags are most common in requirements
   - Multiple match scenarios (how often?)

3. **Error patterns**:
   - Most common missing tag combinations
   - Profiles that fail due to expired sessions
   - Activities that consistently can't find profiles

### Logging

**Standard format**:
```python
# Successful resolution
log.info(
    f"Profile resolved: name='{profile_name}', "
    f"required_tags={required_tags}, "
    f"resolution_method={'exact'|'tags'|'temp'}, "
    f"duration_ms={elapsed_ms}"
)

# Failed resolution
log.error(
    f"Profile resolution failed: "
    f"required_tags={required_tags}, "
    f"available_profiles={profile_count}, "
    f"closest_match={closest_profile_name} (missing_tags={missing_tags})"
)
```

---

## Future Enhancements

### 1. **Profile Capabilities Declaration** (v0.5.0)

Allow profiles to declare what they can do:
```json
{
  "name": "My_Amazon",
  "capabilities": {
    "can_purchase": true,
    "can_access_orders": true,
    "can_manage_account": false,
    "max_purchase_amount": 100.00
  }
}
```

Cloud can require specific capabilities:
```json
{
  "required_capabilities": {
    "can_purchase": true,
    "max_purchase_amount": {"min": 50.00}
  }
}
```

### 2. **Profile Registry Service** (v1.0.0)

**Optional** centralized service for organizations:
- Admins can see which profiles exist across all clients (names hidden)
- Aggregate view of capability coverage
- Detect gaps: "No profiles for salesforce.com with admin tag"
- Does NOT store credentials or actual profile data
- Read-only view for planning purposes

### 3. **Smart Load Balancing** (v1.0.0)

When multiple profiles match:
- Track current load per profile
- Route to least-loaded profile
- Health-check profiles before selection
- Automatic failover if profile session expires

### 4. **Profile Templates** (v0.6.0)

Pre-configured profile templates for common services:
```bash
python profile_manager.py create-from-template \
  --template "amazon-buyer" \
  --profile "My_Amazon"

# Automatically sets tags: [amazon.com, authenticated, buyer]
# Suggests auto-login sites: [amazon.com]
# Sets default timeout: 24 hours
```

---

## Success Criteria

### Phase 1 (v0.2.0) - Complete When:

✅ Cloud can send `required_tags` instead of `profile_name`
✅ Client resolves tags to local profiles successfully
✅ Exact `profile_name` still works (backward compatible)
✅ Error messages guide users on missing profiles
✅ All existing scripts continue to work

### Phase 2 (v0.3.0) - Complete When:

✅ UI has tag selector with autocomplete
✅ Documentation includes tag taxonomy and examples
✅ Migration guide helps users add tags to existing profiles
✅ Cloud template examples use `required_tags`

### Phase 3 (v0.4.0) - Complete When:

✅ Smart matching handles multiple profile matches
✅ Session expiry detection prevents using stale profiles
✅ Monitoring dashboard shows resolution metrics

---

## Appendix: Code Snippets

### A. Profile Resolution Function (Python)

```python
def resolve_profile(command: Dict[str, Any], profile_manager) -> Optional[Dict[str, Any]]:
    """
    Resolve which local profile to use based on cloud requirements.

    Priority:
    1. Exact profile_name match (if provided)
    2. Tag-based matching (required_tags with AND logic)
    3. Temporary profile (if allowed)
    4. Error (no suitable profile found)

    Args:
        command: Activity task payload from cloud
        profile_manager: ProfileManager instance

    Returns:
        Profile dict with name, user_data_dir, tags, etc.
        None if using temporary profile

    Raises:
        ProfileNotFoundError: No suitable profile found and temp not allowed
    """
    session_config = command.get('session', {})

    # Priority 1: Try exact name match (backward compatibility)
    profile_name = session_config.get('profile_name')
    if profile_name:
        try:
            profile = profile_manager.get_profile(profile_name)
            log.info(f"✓ Resolved profile by exact name: '{profile_name}'")
            return profile
        except ProfileNotFoundError:
            log.warning(f"Profile '{profile_name}' not found, trying tag matching...")

    # Priority 2: Try tag-based matching (all required tags must match)
    required_tags = session_config.get('required_tags', [])
    if required_tags:
        # Get profiles that have ALL required tags
        matched_profiles = profile_manager.find_profiles_by_tags(
            required_tags=required_tags,
            match_all=True  # AND logic, not OR
        )

        if matched_profiles:
            # Use first match (future: sort by last_used, pick most recent)
            selected_profile = matched_profiles[0]
            log.info(
                f"✓ Resolved profile by tags: '{selected_profile['name']}' "
                f"(matched tags: {required_tags})"
            )
            return selected_profile

        log.warning(f"No profiles found matching all required tags: {required_tags}")

    # Priority 3: Check if temporary profile allowed
    allow_temp = session_config.get('allow_temp_profile', True)
    if allow_temp:
        log.info("Using temporary profile (no persistent session)")
        return None  # None signals temp profile to caller

    # Priority 4: Nothing matched and temp not allowed - ERROR
    # Build helpful error message
    all_profiles = profile_manager.list_profiles()
    error_details = {
        "required_tags": required_tags,
        "requested_name": profile_name,
        "available_profiles": [
            {
                "name": p["name"],
                "tags": p["tags"],
                "missing_tags": list(set(required_tags) - set(p["tags"]))
            }
            for p in all_profiles
        ]
    }

    raise ProfileNotFoundError(
        f"No suitable profile found. "
        f"Required tags: {required_tags}, "
        f"Requested name: {profile_name}",
        details=error_details
    )
```

### B. Tag Matching in ProfileManager (Python)

```python
def find_profiles_by_tags(
    self,
    required_tags: List[str],
    match_all: bool = True
) -> List[Dict[str, Any]]:
    """
    Find profiles that match the required tags.

    Args:
        required_tags: List of tags to match
        match_all: If True, profile must have ALL required tags (AND logic)
                   If False, profile must have ANY required tag (OR logic)

    Returns:
        List of profile dicts that match the criteria
    """
    profiles = self.list_profiles()
    matched = []

    for profile in profiles:
        profile_tags = set(profile.get("tags", []))
        required_set = set(required_tags)

        if match_all:
            # AND logic: profile must have ALL required tags
            if required_set.issubset(profile_tags):
                matched.append(profile)
        else:
            # OR logic: profile must have ANY required tag
            if required_set.intersection(profile_tags):
                matched.append(profile)

    return matched
```

### C. Cloud Template Example (JSON)

```json
{
  "name": "Amazon Product Research",
  "description": "Extract product details from Amazon search results",
  "session": {
    "required_tags": ["amazon.com", "authenticated", "read-only"],
    "profile_name": "amazon_default",
    "allow_temp_profile": false,
    "session_timeout_hours": 24,
    "wait_for_human_login": false
  },
  "starting_page": "https://www.amazon.com",
  "steps": [
    {
      "action": "act",
      "description": "Search for product",
      "prompt": "Search for 'wireless headphones' and click search"
    },
    {
      "action": "act_with_schema",
      "description": "Extract product details",
      "prompt": "Extract the title, price, and rating of the first 5 products",
      "schema": {
        "type": "object",
        "properties": {
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "title": {"type": "string"},
                "price": {"type": "string"},
                "rating": {"type": "number"}
              }
            }
          }
        }
      }
    }
  ]
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Claude + Guy | Initial design document |

---

## References

- Profile Manager Implementation: `python/profile_manager.py`
- Script Executor: `python/script_executor.py`
- Nova Act Wrapper: `python/nova_act_wrapper.py`
- Step Functions Activity API: AWS Documentation
- Windows Improvements Design: `WINDOWS_IMPROVEMENTS.md`
