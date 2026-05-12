# AI Teaching Assistant Skill

An MCP-backed skill that lets Claude agents inside a NemoClaw / OpenShell
sandbox interact with the AgenticTA study platform running on the host machine.

---

## IMPORTANT — Agent Routing Rules

Follow these rules **before** choosing any tool:

| If the user asks… | Call this tool |
|---|---|
| to upload / add / share a PDF | **`get_upload_link`** — gives them a browser URL |
| to upload an image / photo / diagram and ask about it | **`get_image_upload_link`** — gives them a browser URL |
| about their study topics / subtopics | `list_subtopics` then `chat_message` |
| to generate / create a curriculum | `generate_curriculum` |
| to take a quiz / be tested | `list_subtopics` → `generate_quiz` → `submit_quiz` |
| a study question about the material | `chat_message` |
| to book a study session | `book_calendar` |
| for YouTube / video recommendations | `youtube_search` |

**Never ask the user for a file path.** Always call `get_upload_link` or `get_image_upload_link` for uploads.
The user cannot access the host filesystem — they upload via their browser.

---

## PDF Upload Flow

When a user says anything like *"upload a PDF"*, *"add my notes"*, *"I have a file"*:

1. Call **`get_upload_link(user_id)`** — returns a browser URL.
2. Show the URL to the user: *"Please open this link to upload your PDF: [URL]"*
3. Wait for the user to say *"done"* or *"uploaded"*.
4. Call **`generate_curriculum(user_id)`** to process the uploaded file.

> **Remote host / WSL users**: if the link uses `localhost`, replace it with
> `127.0.0.1` in your browser — e.g. `http://127.0.0.1:8000/upload?user_id=...`
> WSL port-forward tunnels may not resolve `localhost` correctly on Windows.
> Port 8000 must be forwarded: `brev port-forward <instance-name> -p 8000:8000`

---

## Image Upload + VLM Flow

When a user says anything like *"here's a diagram"*, *"look at this image"*, *"explain this screenshot"*, *"I have a photo to show you"*:

1. Call **`get_image_upload_link(user_id, message="<their question>")`** — returns a browser URL.
   - Pass the user's question as `message` to pre-fill the form.
2. Show the URL to the user: *"Please open this link to upload your image: [URL]"*
3. User opens the page, uploads their image, reviews/edits the question, clicks **Ask Study Buddy**.
   - The page automatically loads their chapter, subtopic, memory, and history context.
   - The VLM answer is shown on the page immediately.
4. Wait for the user to say *"done"*.
5. Call **`get_last_vlm_response(user_id)`** — retrieves the stored answer into the conversation.

> **Remote host / WSL users**: if the link uses `localhost`, replace it with
> `127.0.0.1` in your browser — e.g. `http://127.0.0.1:8000/upload-image?user_id=...`
> WSL port-forward tunnels may not resolve `localhost` correctly on Windows.
> Port 8000 must be forwarded: `brev port-forward <instance-name> -p 8000:8000`

---

## Invocation

```bash
$SKILL_DIR/venv/bin/python3 $SKILL_DIR/scripts/ta_client.py <tool> [--args]
```

## First-Time Setup

```bash
$SKILL_DIR/venv/bin/python3 $SKILL_DIR/scripts/setup_config.py
# or non-interactively:
$SKILL_DIR/venv/bin/python3 $SKILL_DIR/scripts/setup_config.py \
  --user-id alice --server-url http://host.openshell.internal:8999/mcp
```

## Configuration (`config.json`)

```json
{
  "user_id": "alice",
  "server_url": "http://host.openshell.internal:8999/mcp"
}
```

When `config.json` exists, `--user-id` and `--server-url` are optional on every call.

---

## Available Tools

| Tool | When to use |
|------|-------------|
| `get_upload_link` | **User wants to upload a PDF** — always use this, never ask for a path |
| `get_image_upload_link` | **User wants to share an image/diagram** and ask a VLM question about it |
| `get_last_vlm_response` | After user confirms image submission — retrieves stored VLM answer |
| `check_ingest_status` | Verify a PDF has been ingested before generating curriculum |
| `generate_curriculum` | After upload confirmed — builds the personalised study plan |
| `get_curriculum` | Retrieve the current curriculum |
| `list_subtopics` | List chapter subtopics with indices (required before quiz tools) |
| `chat_message` | Any study question or conversation about the material |
| `generate_quiz` | Create MCQ quiz for a specific subtopic |
| `submit_quiz` | Grade answers — accepts A/B/C/D or 0/1/2/3 |
| `book_calendar` | Natural-language → .ics calendar event |
| `youtube_search` | Find supplementary educational videos |
| `health_check` | Verify the Teaching Assistant API is reachable |
| `delete_user_data` | Wipe a user's data before re-uploading a PDF |
| `upload_pdf` | ⚙️ Admin/automation only — PDF must already exist on the host filesystem |

---

## Typical Workflow

```bash
SKILL="$SKILL_DIR/venv/bin/python3 $SKILL_DIR/scripts/ta_client.py"

# 1. Get upload link and share it with the user
$SKILL get_upload_link --user-id alice
# → Returns a browser URL. User opens it, uploads their PDF, says "done".

# 2. Generate curriculum (after user confirms upload)
$SKILL generate_curriculum --user-id alice

# 3. List subtopics
$SKILL list_subtopics --user-id alice

# 4. Chat with study buddy
$SKILL chat_message --user-id alice --message "Explain the first topic"

# 5. Take a quiz on subtopic 0
$SKILL generate_quiz --user-id alice --subtopic-number 0
$SKILL submit_quiz   --user-id alice --subtopic-number 0 --answers "B,A,C"

# 6. Book a study session
$SKILL book_calendar --user-id alice --text "Study session tomorrow at 3pm for 1 hour"

# 7. Search for supplementary videos
$SKILL youtube_search --query "machine learning gradient descent"

# 8. Get image upload link (user wants to share a diagram)
$SKILL get_image_upload_link --user-id alice --message "What does this diagram show?"
# → Share URL with user. User uploads image & submits. User says "done".

# 9. Retrieve VLM answer into the conversation
$SKILL get_last_vlm_response --user-id alice
```

---

## Server URL

Default: `http://host.openshell.internal:8999/mcp`

The MCP server must be running on the host:

```bash
python3 ai_teaching_assistant_mcp_server.py
```
