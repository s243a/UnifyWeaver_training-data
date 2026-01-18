# Prerequisites Interface

Special semantic interface for setup, environment, and foundational knowledge content.

## Purpose

The prerequisites interface provides a focused view of content that readers need before engaging with education chapters or using UnifyWeaver features. This includes:

- **Environment Setup** - Tool installation, configuration
- **Background Knowledge** - Concepts assumed but not taught
- **Common Setup** - Shared across multiple chapters/books

## Interface Definition

```json
{
  "name": "prerequisites",
  "description": "Setup, environment, and foundational knowledge",
  "topics": ["installation", "setup", "environment", "configuration", "background"],
  "is_meta_interface": true
}
```

## Content Categories

### 1. Tool Installation

```
prerequisites/
├── prolog-installation.jsonl      # SWI-Prolog setup
├── python-setup.jsonl             # Python 3.9+ with dependencies
├── dotnet-setup.jsonl             # .NET SDK for C# target
├── go-setup.jsonl                 # Go toolchain
└── rust-setup.jsonl               # Rust toolchain
```

### 2. Environment Configuration

```
prerequisites/
├── unifyweaver-clone.jsonl        # Cloning and project structure
├── path-configuration.jsonl       # PATH setup for scripts
├── editor-setup.jsonl             # Recommended editor configs
└── terminal-setup.jsonl           # Shell requirements
```

### 3. Background Knowledge

```
prerequisites/
├── programming-basics.jsonl       # Variables, functions, control flow
├── command-line-basics.jsonl      # Terminal navigation, commands
├── logic-programming-intro.jsonl  # Declarative vs imperative
└── data-formats.jsonl             # JSON, JSONL, CSV, XML basics
```

## JSONL Format

Each prerequisite cluster:

```json
{
  "cluster_id": "prereq-prolog-installation",
  "source_file": "prerequisites/prolog-installation.jsonl",
  "source_type": "prerequisite",
  "category": "tool_installation",
  "platform": ["linux", "macos", "windows"],
  "answer": {
    "text": "Install SWI-Prolog on your system...",
    "code_blocks": [
      {
        "language": "bash",
        "code": "# Ubuntu/Debian\nsudo apt-get install swi-prolog\n\n# macOS\nbrew install swi-prolog\n\n# Windows\nwinget install SWI-Prolog.SWI-Prolog",
        "executable": true,
        "platform_specific": true
      }
    ],
    "verification": {
      "command": "swipl --version",
      "expected_pattern": "SWI-Prolog"
    }
  },
  "questions": [
    {"text": "How do I install SWI-Prolog?", "type": "practical"},
    {"text": "What Prolog implementation does UnifyWeaver use?", "type": "concept"},
    {"text": "How do I verify Prolog is installed correctly?", "type": "troubleshooting"}
  ],
  "required_by": [
    "book-01-ch02",
    "book-01-ch03",
    "book-11-prolog-target"
  ]
}
```

## Relation Types

Prerequisites connect to chapters via:

| Relation | Meaning |
|----------|---------|
| `foundational` | Prerequisite provides foundation for chapter |
| `preliminary` | Prerequisite must be completed before chapter |

```json
{
  "from": "prereq-prolog-installation",
  "to": "book-01-ch02",
  "type": "preliminary",
  "required": true
}
```

## Querying Prerequisites

```python
from kg_topology_api import KGTopologyAPI

db = KGTopologyAPI('training-data/unified.db')

# Get all prerequisites for a chapter
chapter = db.get_cluster_by_id('book-01-ch02')
prereqs = db.get_foundational(chapter['cluster_id'])

# Search prerequisites interface directly
results = db.search_via_interface(
    query_text="How do I install Prolog?",
    interface_name="prerequisites"
)

# Check if reader has completed prerequisites
def check_prerequisites(chapter_id, completed_prereqs):
    required = db.get_relations(
        to_answer_id=chapter_id,
        relation_type='preliminary'
    )
    missing = [r for r in required if r['from'] not in completed_prereqs]
    return missing
```

## Verification Commands

Each tool prerequisite includes verification:

```json
{
  "verification": {
    "command": "swipl --version",
    "expected_pattern": "SWI-Prolog \\d+\\.\\d+",
    "success_message": "SWI-Prolog is installed correctly",
    "failure_message": "SWI-Prolog not found. Please install it first."
  }
}
```

## Platform-Specific Content

Prerequisites can be platform-specific:

```json
{
  "platform": ["linux"],
  "code_blocks": [
    {
      "language": "bash",
      "code": "sudo apt-get install swi-prolog",
      "platform": "linux-debian"
    }
  ]
}
```

Or cross-platform with variants:

```json
{
  "platform": ["linux", "macos", "windows"],
  "code_blocks": [
    {
      "language": "bash",
      "code": "# Platform-specific commands\n...",
      "variants": {
        "linux-debian": "sudo apt-get install swi-prolog",
        "linux-arch": "sudo pacman -S swi-prolog",
        "macos": "brew install swi-prolog",
        "windows": "winget install SWI-Prolog.SWI-Prolog"
      }
    }
  ]
}
```

## Usage in Chapter Review

When the LLM reviews a chapter using `chapter_review_playbook.md`, it:

1. Identifies prerequisites from chapter content
2. Checks if prerequisite clusters exist
3. Creates relations to existing prerequisites
4. Flags missing prerequisites for creation

```json
{
  "prerequisites": {
    "existing": ["prereq-prolog-installation"],
    "missing": ["prereq-basic-recursion-understanding"],
    "relations": [
      {"to": "prereq-prolog-installation", "type": "preliminary", "required": true}
    ]
  }
}
```
