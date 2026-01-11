# Claude Writer

Talk through your ideas; Claude interviews you and produces written content.

## Quick Start

### 1. Get the code

Download this project to your computer:
- **Option A**: On GitHub, click the green "Code" button → "Download ZIP" → unzip it
- **Option B**: If you have git: `git clone https://github.com/your-username/claude_writer.git`

### 2. Install Claude Code

Download Claude Code from [claude.ai/download](https://claude.ai/download). This is the AI assistant that powers everything.

### 3. Open the project

Launch Claude Code. It will ask you to open a folder; select the `claude_writer` folder you downloaded.

### 4. Run setup (one time)

In the Claude Code chat, type:
```
./scripts/init.sh
```

This installs the required tools. You only need to do this once.

### 5. Configure Gemini API (optional)

Some features use Google Gemini for text and image generation:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into the `.env` file (replace `your-api-key-here`)

**Free tier**: Text generation works without billing (1000 requests/day).

**Paid tier**: Image generation requires billing. Enable at [Google Cloud Console](https://console.cloud.google.com/billing). Images cost ~$0.03 each.

### 6. Start ideating

Type `/ideate` and describe what you want to explore. Claude will interview you, capture your ideas, and help you produce content.

---

## How It Works

Claude Code is an AI assistant that runs in your terminal. You type messages; it responds, reads files, and runs the custom commands defined in this project.

**Voice input recommended**: Talking is faster than typing. Try [Wispr Flow](https://wisprflow.ai/) or your system's dictation.

**The workflow**:
1. Create an "Idea Space": run `/ideate` to explore and capture ideas through conversation in custom "Idea Spaces." Treat each idea space as a knowledge base of everything you've talked about in that idea over time. After you've completed a conversation with Claude using the `/ideate` command, run `/generate_transcript` to create a transcript of that convo and ideas into that Idea Space. `/ideate` will do this for you the first time you run it.
2. `/generate-view` turns captured ideas into polished content (blog posts, briefs, essays). YOu can generate infinite views on a single Idea Space. Specialized view generators (`/generate-poem-view`, etc.) aid in creating more powerful views.

Your ideas and their views live in the `ideas/` folder. Each idea gets its own space with transcripts, assets, and views. Anything is regenerable at any time.

---

## Commands

| Command | What it does |
|---------|--------------|
| `/ideate` | Explore an idea through guided conversation |
| `/generate-transcript` | Save the current conversation |
| `/generate-view` | Create content (blog post, brief, essay, etc.) |
| `/generate-poem-view` | Generate poetry |
| `/generate-academic-infographic-view` | Create infographic specifications |
| `/generate-new-view` | Build a new content generator |

---

## Project Structure

```
claude_writer/
├── ideas/           # Your idea spaces
├── templates/       # Voice and format references
├── scripts/         # Setup and utility scripts
└── .claude/
    ├── commands/    # User-invoked commands
    ├── agents/      # Autonomous subagents
    └── skills/      # Utilities (gemini, etc.)
```
