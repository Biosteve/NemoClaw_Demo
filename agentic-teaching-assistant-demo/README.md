# AgenticTA — AI Study Buddy

An AI teaching assistant that turns your PDFs into a personalised study experience.

## Features

- PDF upload → curriculum + study materials
- Study buddy chat with agentic memory
- Quiz generation per subtopic
- Calendar booking (natural language → .ics)
- Image upload + Q&A
- YouTube video search for study topics
- Study break games

## Get Started

```bash
cp .env.example .env   # add your NVIDIA_API_KEY
make setup
make up
make gradio
# open http://localhost:7860
```

See **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for full setup, RAG stack, and troubleshooting.

## Requirements

- Docker + Docker Compose v2
- [NVIDIA API Key](https://build.nvidia.com)

## Commands

```bash
make help          # all commands
make up            # start (Option A — direct PDF, no RAG)
make up-with-rag   # start with full RAG stack (Option B)
make gradio        # launch UI at http://localhost:7860
make games-up      # study break games at http://localhost:8080
make down          # stop everything
```
