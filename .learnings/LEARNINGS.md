## [LRN-20260304-001] configuration_issue

**Logged**: 2026-03-04T08:59:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
Self-improvement skill was installed but not functioning because it was placed in the wrong directory.

### Details
The skill was cloned to `~/.openclaw/skills/self-improving-agent` (global skills directory), but OpenClaw only loads skills from the workspace's `skills/` folder (`~/.openclaw/workspace/skills/`). This caused the skill to be available in the repository but not injected into agent sessions.

### Suggested Action
- Copy the skill to `workspace/skills/` (or install via clawhub into correct location)
- Configure OpenClaw hooks for automatic activation
- Verify by checking that `.learnings/` entries are populated during sessions

### Metadata
- Source: user_feedback
- Related Files: `~/.openclaw/workspace/.learnings/`
- Pattern-Key: infra.skill_placement
- Recurrence-Count: 1
- First-Seen: 2026-03-04
- Last-Seen: 2026-03-04
