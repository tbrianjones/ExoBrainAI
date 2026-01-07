# Agent-Driven Writing System: Initial Setup and Vision

- person: T. Brian Jones
- ai: Claude Opus 4.5
- emotional analysis: visionary, confident, building momentum; clear sense of what the system should feel like; practical focus on voice-driven interaction

## Ideas & Themes

- **Layered Writing Stack**: Writing exists as a hierarchy: topic → outline → chapters → paragraphs → sentences. Edits at any layer can propagate downward. Change the topic idea and agents regenerate the outline and prose. Move a section in the outline and the system rewrites accordingly. You can also edit at any specific level without affecting higher layers.

- **Filesystem as Database**: All content lives in markdown files tracked by git. Written documents are versioned like source code. Edits are commits. History is preserved. No external database; the file structure is the data model.

- **Interview-Driven Content**: The system interviews you rather than expecting you to write. You don't face blank pages; you answer questions. Claude asks, you talk, the system captures and structures. The raw conversation becomes transcripts; the refined output becomes views.

- **Agent-Managed Everything**: Specialized agents handle different tasks: interviewing, writing, editing, voice matching. You can deploy different agents (journalist style, Ezra Klein style, your personal voice) to edit at any level. The user only talks; agents produce.

- **Meta-Level Controls**: Style, tone, humor, technical depth, and narrative threading are configurable per project. Assets (characters, settings, items) persist across a work. Writing styles can be learned from samples.

- **Voice Over Typing**: The gold standard is speaking to your computer, not typing. Using a voice interface like Wispr Flow produces up to 10x more content. Speaking is more fluid; you share more; ideas come out better.

- **Future Interface Vision**: A document editor like Google Docs but different. Commenting section where agents can come in and edit. You can point agents at sections, chapters, or the whole work. The interface is for directing agents, not necessarily for direct text editing.

- **Structured Language History**: An underlying concept where the actual written language is structured in a way where the history of it is tracked. This is future work but part of the broader vision.

## Transcript Summary

### The Core Vision

T. Brian described a writing utility for himself and eventually broader use. The system manages writing at every layer of its stack. "At any point, you can come in and edit a particular sentence; you could edit a paragraph; you could delete a paragraph... If you change the topic idea, agents could then propagate that shift down through the outline in the writing."

The key insight: writing should be editable at any level of abstraction, and changes should be able to cascade through the system.

### Meta Controls and Assets

The system needs to manage meta aspects: style, humor, technical depth, storyline threading, and assets like characters, settings, and items. Previous writing samples go into a folder to generate writing styles; these might become skills that capture voice.

"I want everything to be generateable by agents, manageable by agents. I only want to talk to this system."

### The Interview Model

"Treat this as a system that will interview me as I'm writing things, and that I can inject into." The system asks questions to draw out ideas rather than expecting the user to write directly. This maps to the generate-idea command's podcast-producer interview approach.

### Voice as Primary Interface

"A primary focus of this library is that the gold standard is you should not be doing anything yourself; you should only be ideating, and in particular you should be talking to your computer."

T. Brian strongly encourages voice interfaces like Wispr Flow over typing: "It's more fluid, you get your ideas out better, and you share a lot more, up to ten times more, I've found in my own use cases."

### Agent Diversity

"I could have a journalist agent come in, I could have an Ezra Klein agent come in, I could have my own personal agent come in, I could have them edit sections, I could have them edit chapters." Multiple specialized agents with different voices and approaches can work on the same content.

### Future Interface

The envisioned interface is "kind of like a document editor, like Google Docs, but you can use this editor differently. I won't be editing the text necessarily, although you could also do that. But you will have a commenting section like you do in Google Docs, but agents can come in and edit them and you can actually point agents at this."

### Folder Structure Decisions

The MVP structure emerged through the conversation:
- `.claude/commands/` for command definitions (generate-idea, generate-transcript, generate-view)
- `ideas/` for idea spaces with numbered folders (NNNN-name format)
- Each idea folder contains: README.md, assets/, transcripts/, views/
- `templates/styles/` for writing style references
- `doc_load/` for source material and writing samples

### Content Production Guidelines

Explicit instruction to avoid dashes and double dashes in generated prose: "a very common pattern of AI-generated content." Instead, use semicolons to join clauses or introduce pivots, and ellipses sparingly to indicate pause or trailing off.

## Full Transcript

### Initial Prompt

**T. Brian:** This is a brand new repo I just opened you in. I want to tell you what it's about, and then I want you to kind of set up the repo. This is a project specifically to build out a writing utility for myself, but then eventually for broader use. The idea is we will set up commands and agents and skills, et cetera, Claude skills, agents, and commands that are then leveraged to ideate and outline and write articles or books or short stories. The general concept is that as you write a story, all of the layers of it can and should be managed and manageable so that you can edit it at any level of its writing stack. For instance, you might just have a topic idea that might evolve over time, and if you change the topic idea, agents could then propagate that shift down through the outline in the writing. If you change the outline, you could have agents propagate that out to the writing and regenerate the writing where it's changed, or you could move a topic in an outline, and then the system would redo the writing structured in that capacity. So at any point, you can come in and edit a particular sentence; you could edit a paragraph; you could delete a paragraph at any level.

As part of that structurally, some things we'll want to be able to control are meta aspects of this, like: What is the style? Is there humor in it? Should it be technical? Should it have a storyline that goes through? Are there assets involved like characters, settings, items?

Then also part of the feed here is going to be writing styles, so another meta thing that's probably in the library but not in a particular writing asset would be things like previous writing of mine that I throw into a folder that we then turn into a skill, perhaps. I want everything to be generateable by agents, manageable by agents. I only want to talk to this system, treat this as a system that will interview me as I'm writing things, and that I can inject into. At some point, it will have an interface on the front end that's kind of like a document editor, like Google Docs, but you can use this editor differently. I won't be editing the text necessarily, although you could also do that. But you will have a commenting section like you do in Google Docs, but agents can come in and edit them and you can actually point agents at this. I could have a journalist agent come in, I could have an Ezra Klein agent come in, I could have my own personal agent come in, I could have them edit sections, I could have them edit chapters.

And underlying ultimately there's this concept that I've been playing with where the actual written language is structured in a way where the history of it is tracked. That's probably getting ahead of myself, I want to get this basic structure set up. I want you to take what I've said here and just synthesize it. Think about it for a second. Then I want you to set yourself up in this repo.

---

### Q1: Clarifying the MVP Structure

**T. Brian:** I have done a lot of work in this repo. I want you to scan the whole thing and get a better understanding of how it's structured right now. This is the MVP structure that I want.

There's a .Claude folder that has Claude agents and Claude commands in it. There are no agents yet, but there are three commands we've created. Check those out and understand what they are.

There's an Ideas folder where actual concepts go to live. You'll see two of them in there. The 0000 agent, "ideation-driven content production," is actually this content thread; it's this project. Then the "Consciousness in the Age of AI" is a thread that I created with another agent using the generate-idea, generate-view, and generate-transcript commands.

You'll also see a templates folder that is living but doesn't have anything in it yet. The idea there is to be able to throw external stuff there to generate writing styles and templates of views for articles I want to produce, or how to produce a tweet or an Instagram post or a blog post or a research paper.

Within the IDEAS folder, each idea is generated via the generate-idea command, and when that happens, it generates that folder, plus folders inside of that: assets, transcripts, and views, plus a README.md. Assets are where things live, like characters, settings, or concepts that I want to flesh out and be explicit about. Transcripts are just raw information conversations with AI that are then written in there. And then views are actual pieces of content that are created, and they're just named by themselves, and then inside of them they have some structure that speaks to sort of how it was produced, who it was produced for, what styles to have, and then the actual content.

---

### Q2: Documentation Requirements

**T. Brian:** From all this, I want you to review the CLAUDE.md and README.md files and update them. Specifically, CLAUDE.md should be very specific to just how an agent should work in this library. It doesn't need to be descriptive about too much stuff, but just the context an agent needs to have to work in this library. Then, specifically, I also want a very specific section in there about content production. I want you to add a note that you should very, very much limit the use of dashes and double dashes, a very common pattern of AI-generated content. I don't want those in the writing. Instead, you can use semicolons and ellipses (the three periods) to kind of introduce pause or flow control flow during a written article.

In the README.md, I want an overview of all the details of how the application works, its structure, its file structure, how it's built, why it's built, and then, specifically, up at the top, a section on how to use this. The way to use it is to clone the library locally, spin up Claude inside of it, and then run generate-idea. Generate-idea will do most of the other stuff, but to know that those tools are in there and describe what the three of them are. To get started, just say to Claude, "I want to generate a new idea." Use the generate-idea command and talk to me about it. Here's my idea, and it can be brief. Then the generate-idea will interview you and produce all the content. After having a long conversation like this one, you can run generate-transcript and it'll produce a transcript inside of an ideas folder, and if you want to produce a particular piece of content, you can just run generate-view and it'll work with you to outline and define that.

---

### Q3: The Gold Standard

**T. Brian:** One other note I want explicitly in the README.md right at the top that a primary focus of this library is that the gold standard is you should not be doing anything yourself; you should only be ideating, and in particular you should be talking to your computer. This will work fine if you type at the command line, you type with your agent, but I strongly encourage you to use something like Wispr Flow, where you can speak to the computer. It's more fluid, you get your ideas out better, and you share a lot more, up to ten times more, I've found in my own use cases.
