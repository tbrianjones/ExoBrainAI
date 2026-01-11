# Idea Writer Setup Guide

Set up Idea Writer in Claude.ai using Projects. This gives you a persistent workspace where your ideas, transcripts, and generated content accumulate over time.

## What You Need

- Claude Pro or Max subscription (Projects require a paid plan)
- 10 minutes for initial setup

## Step 1: Create a New Project

1. Go to [claude.ai](https://claude.ai)
2. Click **"Projects"** in the left sidebar
3. Click **"New Project"**
4. Name it something like "Idea Writer" or "My Ideas"

## Step 2: Add Custom Instructions

1. In your new project, click **"Edit project details"** (pencil icon)
2. Scroll to **"Custom instructions"**
3. Open the file `CUSTOM_INSTRUCTIONS.md` from this folder
4. Copy everything below the `---` line
5. Paste it into the Custom Instructions field
6. Click **Save**

## Step 3: Add Voice Templates (Optional)

Voice templates help Claude match your preferred writing style.

1. In your project, click **"Add content"** (or the + icon)
2. Select **"Upload files"**
3. Upload the voice template files from `skill/templates/voices/`:
   - `professional-communication.md`
   - `conversational-expert.md`
   - `exploratory-thinker.md`
4. These will appear in your Knowledge Base

## Step 4: Start Ideating

1. Click **"New chat"** within your project
2. Say: **"Let's ideate on [your topic]"**
3. Claude will interview you with thoughtful questions
4. When finished, say: **"Capture this as a transcript"**

## Step 5: Save Your Work

After Claude creates an artifact:

1. Click on the artifact to expand it
2. Click the **download icon** (bottom right of artifact)
3. Save the file to your computer
4. Back in your project, click **"Add content"** → **"Upload files"**
5. Upload the transcript you just downloaded

Now Claude can reference this transcript in future conversations!

## The Complete Workflow

```
1. IDEATE
   Say "Let's ideate on X"
   → Claude interviews you
   → Say "Capture this"
   → Download transcript artifact
   → Upload to Knowledge Base

2. BUILD CONTEXT (repeat step 1)
   Each transcript adds to your idea space
   Claude references all uploaded transcripts

3. GENERATE CONTENT
   Say "Generate a blog post about X"
   → Claude reads your transcripts
   → Creates polished content artifact
   → Download to keep
```

## Tips for Best Results

**Keep transcripts in Knowledge Base**: The more context Claude has, the better your generated content will be.

**One project per major idea**: If you have very different topics, consider separate projects.

**Use voice templates**: Upload them once, then say "Use the conversational expert voice" when generating content.

**Name artifacts clearly**: Use dates and topics so you can find things later.

## Folder Organization (Optional)

If you want to keep local copies organized:

```
my-ideas/
├── idea-name/
│   ├── readme.md
│   ├── transcripts/
│   │   ├── transcript-2026-01-11-initial.md
│   │   └── transcript-2026-01-15-deeper.md
│   └── views/
│       ├── view-blog-post.md
│       └── view-executive-brief.md
└── templates/
    └── voices/
```

## Troubleshooting

**Claude doesn't remember previous conversations**
→ Make sure you're chatting within the Project (not a regular chat)
→ Upload transcripts to the Knowledge Base

**Claude doesn't use my voice template**
→ Say "Use the [name] voice" explicitly
→ Make sure the template file is uploaded to Knowledge Base

**Artifacts aren't saving**
→ Download artifacts manually and re-upload to Knowledge Base
→ Artifacts in chat don't automatically persist to the project

## Next Steps

Once you're comfortable with the basics:

1. Create multiple idea spaces by uploading organized transcripts
2. Try different view types: essays, briefs, scripts, poems
3. Build your own voice templates based on writing you admire
4. Share generated content or continue refining it
