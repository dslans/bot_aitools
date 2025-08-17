Got it ✅ — let’s roll all three features in:

* **Caching** (no repeated AI calls for same URL).
* **Tag extraction** (auto-classify tools).
* **Search & filter** (`/aitools search <keyword>` or `/aitools list <tag>`).
* Also renaming the command to `/aitools`.

---

# 📖 Markdown Plan for Slack AI Tools Wiki Bot

## 1. Overview

A **Slack-integrated wiki with Reddit-style voting**, focused on AI coding tools.
Features:

* Add tools via `/aitools add <title> | <url or description>`.
* AI auto-generates a **summary** and **tags** for each tool.
* Prevent duplicate work with **cache** (entries stored in DB).
* Community **upvotes/downvotes** directly in Slack.
* Browse/search entries with `/aitools search` and `/aitools list`.

---

## 2. Slash Commands

### `/aitools add <title> | <url or description>`

* User submits new entry.
* Bot:

  * Scrapes metadata (if link).
  * Generates **summary** + **tags** with LLM.
  * Caches results in DB (avoids reprocessing duplicate links).
* Responds with:

  ```
  ✅ Added *Roo*
  🔗 https://github.com/some/roo
  📝 Roo is an AI-powered code editing assistant…
  🏷️ Tags: cli, ai-agent, code-editing
  👍 0 | 👎 0
  ```

### `/aitools search <keyword>`

* Searches across:

  * `title`
  * `tags`
  * `ai_summary` text
* Returns top 3–5 matching tools with scores.

### `/aitools list [tag]`

* Lists trending tools:

  * If **no tag**: shows top-ranked entries overall.
  * If **tag provided**: filters by that tag.

---

## 3. Database Schema

```sql
CREATE TABLE entries (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT UNIQUE,               -- for caching
  description TEXT,              -- user-provided
  ai_summary TEXT,               -- cached summary
  tags TEXT[],                   -- auto-extracted tags
  author_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE votes (
  entry_id INT REFERENCES entries(id),
  user_id TEXT,
  vote INT CHECK (vote IN (-1, 1)),
  PRIMARY KEY(entry_id, user_id)
);
```

---

## 4. Google Gen AI Configuration

### Prerequisites

1. **Google Cloud Project**: Create a GCP project and enable the Vertex AI API.
2. **Service Account**: Create a service account with the `Vertex AI User` role.
3. **Authentication**: Set up authentication via one of:
   - Service account key file: `export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"`
   - Application Default Credentials: `gcloud auth application-default login`
4. **Python Dependencies**:
   ```bash
   pip install google-genai slack-bolt psycopg2-binary beautifulsoup4 requests
   ```

### Gemini Model Configuration

```python
from google import genai
from google.genai import types

# Initialize the client with your Google Cloud project
client = genai.Client(
    vertexai=True,
    project="your-project-id",
    location="us-central1"  # or your preferred region
)

# Example function for summary and tag generation
async def generate_summary_and_tags(title, content):
    prompt = f"""
    Analyze this AI coding tool and provide:
    1. A concise summary (max 100 words)
    2. Up to 5 relevant tags for categorization
    
    Tool: {title}
    Content: {content}
    
    Format your response as:
    SUMMARY: [your summary here]
    TAGS: [tag1, tag2, tag3, ...]
    """
    
    # Using Gemini 1.5 Pro for best performance
    response = await client.aio.models.generate_content(
        model="gemini-1.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=500,
        )
    )
    
    return parse_ai_response(response.text)

def parse_ai_response(response_text):
    """Parse the AI response to extract summary and tags."""
    lines = response_text.strip().split('\n')
    summary = ""
    tags = []
    
    for line in lines:
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("TAGS:"):
            tags_str = line.replace("TAGS:", "").strip()
            tags = [tag.strip() for tag in tags_str.split(',')]
    
    return summary, tags
```

---

## 5. Bot Logic (Python + Bolt + Google Gen AI)

### Add Entry

1. Parse input (`title | url/desc`).
2. Check DB → if URL exists, reuse summary/tags.
3. Else scrape + call Google Gen AI (Gemini) → generate summary/tags.
4. Insert into DB.
5. Post formatted message with interactive buttons 👍 👎.

### Voting

* Slack **button actions** → update `votes` table.
* Recompute `score = SUM(vote)` and update Slack message.

### Search

```sql
SELECT e.id, e.title, e.ai_summary, e.tags, COALESCE(SUM(v.vote), 0) AS score
FROM entries e
LEFT JOIN votes v ON e.id = v.entry_id
WHERE e.title ILIKE %keyword%
   OR e.ai_summary ILIKE %keyword%
   OR %keyword% = ANY(e.tags)
GROUP BY e.id
ORDER BY score DESC
LIMIT 5;
```

### List

* Same as above but:

  * If `tag` provided → `WHERE %tag% = ANY(e.tags)`
  * Else → no filter.

---

## 6. Example UX

**Add**

```
/aitools add Aider | https://github.com/paul-gauthier/aider
```

Response:

```
✅ Added *Aider*
🔗 https://github.com/paul-gauthier/aider
📝 Aider is a command-line AI assistant for editing code with GPT models.
🏷️ Tags: cli, code-assistant, pair-programming
👍 0 | 👎 0
```

**Search**

```
/aitools search cli
```

Response:

```
Top results for *cli*:
1. Aider (score: +8) — AI assistant for editing code in terminal.
2. Roo (score: +5) — AI agent that edits repos via chat.
```

**List**

```
/aitools list pair-programming
```

Response:

```
Top tools tagged *pair-programming*:
1. Aider (+8)
2. Roo (+5)
```

---

## 7. Roadmap (Future Enhancements)

* **Approved by Security Policy** (scan our policy and add a line in the response if the tool is approved for work use).
* **Embeddings-based semantic search** (e.g., "test runner" → finds Pytest even if word missing).
* **Web dashboard** (Next.js + Supabase) to browse outside Slack.
* **Weekly digest in Slack** (top new tools).
* **AI comparisons** (ask “compare Roo vs Aider”).

---

✅ At this point, you’ll have a working **Slack wiki with AI-powered summaries, caching, tagging, and community voting**.

---

Do you want me to now **expand the Python code** to include:

* The `/aitools search` and `/aitools list` handlers,
* Plus the **interactive 👍 👎 voting buttons** tied to the DB?
