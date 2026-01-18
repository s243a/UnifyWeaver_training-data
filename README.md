# UnifyWeaver Training Data

Unified semantic knowledge base for UnifyWeaver and UnifyWeaver Education.

## Purpose

This repository contains Q&A training data extracted from:
- UnifyWeaver source code and documentation
- UnifyWeaver Education books and chapters
- Playbooks and examples

The data populates the Knowledge Graph Topology system (see `docs/proposals/ROADMAP_KG_TOPOLOGY.md` in the main project), enabling semantic search and Kleinberg routing across all project content.

## Directory Structure

```
training-data/
├── by-book/             # Original book-organized training data
│   ├── book-01-foundations/
│   ├── book-02-bash-target/
│   ├── ...
│   ├── book-14-ai-training/
│   ├── other-books/
│   ├── prerequisites/
│   ├── tailored/
│   ├── tailored-gemini/
│   └── tailored-gemini-v2/
│
├── by-topic/            # NEW: Task-oriented Q&A (for quickstart agent)
│   ├── quickstart/      # Level 0-1: Identity, capabilities
│   ├── compilation/     # Prolog compilation to targets
│   ├── mindmap/         # Mindmap tools
│   ├── gui/             # App generation, visualization
│   ├── semantic-search/ # Embeddings, models, inference
│   └── security/        # Policy and webapp security
│
├── scripts/             # Data processing scripts
├── unified.db           # SQLite database (generated)
└── README.md
```

### By-Book vs By-Topic

| Organization | Purpose | Use Case |
|--------------|---------|----------|
| `by-book/` | Educational sequence | Learning UnifyWeaver systematically |
| `by-topic/` | Task-oriented | "I want to accomplish X" queries |

The `by-topic/` structure supports the **quickstart agent** - see `docs/design/QUICKSTART_AGENT_*.md` for design details.

### Legacy Clustered Data (for LDA methods)

The original clustered training data (multiple questions per cluster, designed for LDA topic modeling) was removed in favor of higher-quality 1:1 Q&A pairs. The 1:1 format is sufficient for Procrustes projection (our recommended approach) and produces better results.

**Why 1:1 works for Procrustes:** Procrustes projection is mathematically defined even for single input-output mappings, unlike LDA which requires clusters for statistical soundness. When clustering is used with Procrustes, it's for data compression and routing efficiency, not numeric validity.

If you need the clustered format for LDA or similar methods, it's preserved in git history:

**Browse on GitHub:** [ad8b8fe6c32d1d4ffa633792f27ae1575b1dc6c0](https://github.com/s243a/UnifyWeaver_training-data/tree/ad8b8fe6c32d1d4ffa633792f27ae1575b1dc6c0)

```bash
# Last commit with clustered data
git checkout ad8b8fe -- by-book/book-01-foundations/

# Or view what was available
git show ad8b8fe --stat | grep "by-book/book-"
```

## Data Format

### Q&A Clusters (JSONL)

Each `.jsonl` file contains Q&A clusters:

```json
{
  "cluster_id": "book-01-ch02-facts",
  "source_file": "education/book-01-foundations/02_prolog_fundamentals.md",
  "source_type": "education",
  "answer": {
    "text": "A fact is a complex term that is asserted to be true...",
    "code_blocks": [
      {
        "language": "prolog",
        "code": "file_dependency('main.o', 'main.c').",
        "executable": true,
        "line_start": 62
      }
    ]
  },
  "questions": [
    "How do I define a Prolog fact?",
    "What is the syntax for stating that something is true?",
    "Show me a file_dependency example"
  ]
}
```

### Relations (JSONL)

```json
{
  "from_cluster": "book-01-ch02-facts",
  "to_cluster": "book-01-ch03-rules",
  "relation_type": "preliminary",
  "metadata": {"auto_detected": true}
}
```

### Semantic Interfaces

```json
{
  "name": "book-01-foundations",
  "description": "Core Prolog and UnifyWeaver concepts",
  "topics": ["prolog", "facts", "rules", "unification"],
  "clusters": ["book-01-ch01-*", "book-01-ch02-*", "book-01-ch03-*"],
  "prerequisites_interface": "environment-setup"
}
```

## Relation Types

11 relation types from `QA_KNOWLEDGE_GRAPH.md`:

**Learning Flow (4):**
- `foundational` - A is foundational concept for B
- `preliminary` - A is prerequisite step for B
- `compositional` - B extends/builds upon A
- `transitional` - B is natural next step after A

**Scope (2):**
- `refined` - B is more specific variant of A
- `general` - A is broader in scope than B

**Abstraction (5):**
- `generalization` - B is abstract pattern of A
- `implementation` - A is code realizing pattern B
- `axiomatization` - B is abstract theory of A
- `instance` - A is domain satisfying theory B
- `example` - A illustrates/demonstrates B

## Chapter Review Playbook

The `chapter-review-playbook.md` (in main project's `playbooks/`) guides models to:

1. **Test code blocks** - Execute examples, verify they work
2. **Identify gaps** - What's missing or unclear?
3. **Generate questions** - What will readers ask?
4. **Provide answers** - Reference source code, other docs
5. **Map prerequisites** - What must reader know first?
6. **Suggest relations** - Connect to other content

## Semantic Interfaces

### Per-Book Interfaces
Each education book gets an interface for focused search.

### Per-Chapter Interfaces
Fine-grained access to individual chapter content.

### Prerequisites Interface
Special interface for setup/environment content:
- Tool installation
- Environment configuration
- Required background knowledge

### Cross-Cutting Interfaces
Thematic interfaces spanning multiple sources:
- `semantic-search` - Books 13-14 + kg_topology_api.py
- `client-server` - Design docs + service_validation.pl
- `python-pipelines` - python_target.pl + education + playbooks

## Populating Training Data

Training data is populated by LLMs following review playbooks, not by extraction scripts.

### Workflow

1. **LLM reads content** (chapter, source file, playbook)
2. **LLM follows review playbook** to analyze content
3. **LLM generates JSONL** with Q&A clusters, relations, prerequisites
4. **Output stored** in appropriate folder

### Chapter Review

```bash
# Point LLM at a chapter
Read and follow playbooks/chapter_review_playbook.md for:
  education/book-01-foundations/02_prolog_fundamentals.md

# LLM produces:
  training-data/education/book-01-foundations/ch02_prolog_fundamentals.jsonl
```

### Source Review (Future Playbook)

```bash
# Point LLM at source module
Read and follow playbooks/source_review_playbook.md for:
  src/unifyweaver/targets/python_target.pl

# LLM produces:
  training-data/source/targets/python_target.jsonl
```

### Building the Database

After JSONL files are populated:

```bash
# Import all JSONL to unified database
python scripts/import_training_data.py \
    --input training-data/ \
    --output training-data/unified.db \
    --model all-MiniLM-L6-v2
```

## Usage with KG Topology API

```python
from kg_topology_api import KGTopologyAPI

db = KGTopologyAPI('training-data/unified.db')

# Search across all content
results = db.search_with_context(
    "How do I implement fan-out in Python?",
    top_k=5
)

# Search via education interface
results = db.search_via_interface(
    query_text="What are Prolog facts?",
    interface_name="book-01-foundations"
)

# Get prerequisites for a chapter
prereqs = db.get_foundational(chapter_cluster_id)
```

## Pre-computed Embeddings

Pre-computed Q/A embeddings are available on Hugging Face Hub:

**Dataset**: [s243a/unifyweaver-embeddings](https://huggingface.co/datasets/s243a/unifyweaver-embeddings)

| File | Model | Dimensions | Pairs |
|------|-------|------------|-------|
| `tailored_all-minilm_384d_v1_2025-12-25.npz` | all-MiniLM-L6-v2 | 384 | 644 |
| `tailored_modernbert_768d_v1_2025-12-25.npz` | nomic-embed-text-v1.5 | 768 | 644 |

```python
from huggingface_hub import hf_hub_download
import numpy as np

path = hf_hub_download(
    repo_id="s243a/unifyweaver-embeddings",
    filename="tailored_all-minilm_384d_v1_2025-12-25.npz"
)
data = np.load(path)
q_embeddings = data["q_embeddings"]  # (644, 384)
a_embeddings = data["a_embeddings"]  # (644, 384)
```

## License

Training data inherits licenses from source:
- Education content: CC-BY-4.0
- Code examples: MIT OR Apache-2.0
- Source documentation: MIT OR Apache-2.0

## Related

- [UnifyWeaver](https://github.com/s243a/UnifyWeaver) - Main project
- [UnifyWeaver_Education](https://github.com/s243a/UnifyWeaver_Education) - Education books
- [ROADMAP_KG_TOPOLOGY.md](../docs/proposals/ROADMAP_KG_TOPOLOGY.md) - KG Topology design
