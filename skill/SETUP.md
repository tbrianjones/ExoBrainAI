# Claude Writer Setup Guide

Get Claude Writer running with your Claude Max subscription in about 5 minutes.

## Prerequisites

- Claude Pro or Max subscription
- A GitHub account
- A GitHub repository for storing your ideas

## Step 1: Create Your Ideas Repository

If you don't already have one, create a new GitHub repository:

1. Go to [github.com/new](https://github.com/new)
2. Name it something like `ideas` or `claude-writer-ideas`
3. Make it private (recommended) or public
4. Initialize with a README

### Recommended Initial Structure

Create these folders in your new repo:

```
ideas/
templates/
  voices/
```

You can do this by creating placeholder files like `ideas/.gitkeep` and `templates/voices/.gitkeep`.

### Quick Verification Checklist

After your first sync, verify these exist in your repo:
- [ ] `ideas/` folder exists
- [ ] `templates/` folder exists  
- [ ] `templates/voices/` folder exists (optional but recommended)

## Step 2: Enable Skills in Claude

1. Go to [claude.ai/settings/capabilities](https://claude.ai/settings/capabilities)
2. Ensure "Skills" is enabled
3. If using code features, enable "Code execution" as well

## Step 3: Add the Claude Writer Skill

### Option A: From a Shared Link (Easiest)

If someone shared a Claude Writer skill link with you, simply click it to add the skill to your account.

### Option B: Create from This Package

1. In Claude.ai, start a new conversation
2. Say: "I want to create a skill called Claude Writer"
3. Paste the contents of SKILL.md when prompted
4. Claude will set up the skill for you

### Option C: Manual Setup

1. In Claude.ai Settings, go to Skills
2. Click "Create New Skill"
3. Name it "Claude Writer"
4. Paste the contents of SKILL.md

## Step 4: Connect Your GitHub Repository

This is the key step that enables file storage:

1. Start a new conversation in Claude.ai
2. Click the "+" button in the lower left corner
3. Search for or paste your repository URL (e.g., `github.com/yourusername/ideas`)
4. If prompted, authenticate with GitHub
5. Grant Claude access to your repository

**What Claude can do once connected:**
- Read files from your repo
- Create new files and folders
- Update existing files
- Sync changes

**What Claude cannot do:**
- Delete files or folders
- Access repos you haven't explicitly connected

**For private repositories:**
Use HTTPS with a Personal Access Token in the URL format:
`https://<your-token>@github.com/username/repo.git`

Store tokens securely using environment variables or your platform's secrets manager (e.g., Replit Secrets).

## Step 5: Verify It's Working

Start a conversation and say:

> "Let's ideate on a new topic: [your idea]"

Claude should:
1. Check your connected repo for existing ideas
2. Ask if this is new or connects to something existing
3. Begin the interview process
4. Offer to save transcripts to your repo

## Troubleshooting

### "I can't see my repository"

- Make sure you've granted Claude access to the repo
- Try clicking "+" again and re-authenticating
- Check that the repo isn't archived or restricted

### "Claude isn't saving files"

- Verify the GitHub integration is still connected
- Ask Claude: "Can you read the files in my ideas folder?"
- Click "Sync now" to refresh the connection

### "The skill isn't loading"

- Go to Settings → Skills and verify Claude Writer is enabled
- Try saying "Use my Claude Writer skill" explicitly
- Restart the conversation

## Tips for Best Results

1. **Keep one repo for all ideas**: Easier to manage and cross-reference
2. **Use descriptive idea names**: "consciousness-and-ai" beats "idea-1"
3. **Commit the templates**: Having templates in your repo helps Claude stay consistent
4. **Regular syncs**: Click "Sync now" periodically to ensure Claude has the latest

## What's Next?

Once set up, try these commands:

- "Show me my ideas" - List all idea spaces
- "Let's ideate on X" - Start a new session
- "Generate a blog post from [idea]" - Create content
- "What's in the [idea name] space?" - Explore an existing idea

Happy ideating!
