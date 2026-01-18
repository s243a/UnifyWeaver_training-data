# By-Topic Training Data

Task-oriented Q&A data organized by capability domain rather than by book.

## Purpose

This structure supports the **quickstart agent** - helping new users find answers based on what they want to accomplish, not which book/chapter covers it.

## Structure

```
by-topic/
├── quickstart/       # Level 0-1: Identity, capabilities, getting started
├── compilation/      # Prolog compilation to various targets
├── mindmap/          # Mindmap organization and linking tools
├── gui/              # App generation and visualization tools
├── semantic-search/  # Embeddings, models, inference
└── security/         # Policy/firewall and webapp security
```

## File Format

Each `.jsonl` file contains Q&A entries:

```jsonl
{
  "id": "qa_001",
  "question": "How do I compile Prolog to Bash?",
  "question_variants": ["compile prolog to shell", "generate bash from prolog"],
  "level": 3,
  "tree_path": ["Compilation", "Targets", "bash"],
  "answer": "...",
  "related_skills": ["skill_unifyweaver_compile.md"],
  "related_docs": ["docs/EXTENDED_README.md#bash-target"],
  "tags": ["compilation", "bash"]
}
```

## Levels

| Level | Scope | Example |
|-------|-------|---------|
| 0 | Identity | "What is UnifyWeaver?" |
| 1 | Capabilities | "What can I compile to?" |
| 2 | General task | "How do I compile?" |
| 3 | Specific task | "How do I compile to Bash?" |
| 4 | Details | "What flags does Bash target support?" |

## Relationship to By-Book

The `by-book/` folder contains the original training data organized by educational books (book-01-foundations, book-02-bash-target, etc.).

The `by-topic/` folder reorganizes this knowledge around user tasks and can be merged with `by-book/` for training, or used separately for quickstart retrieval.

## See Also

- `../by-book/` - Original book-organized training data
- `docs/design/QUICKSTART_AGENT_*.md` - Design documents for the quickstart system
