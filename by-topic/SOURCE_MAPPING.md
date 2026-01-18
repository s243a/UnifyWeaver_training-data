# Source Mapping for Q&A Generation

Maps capability tree items to relevant source files. Use this to guide Q&A generation.

## How to Use

For each topic, read the listed files and generate Q&A pairs that:
1. Ask questions a new user would ask
2. Answer using information from the source files
3. Reference specific paths for "learn more"

---

## Quickstart (Level 0-1)

### Identity / Overview
| Item | Source Files |
|------|-------------|
| What is UnifyWeaver? | `README.md`, `docs/EXTENDED_README.md` |
| What can it do? | `README.md` (Target Features section) |

---

## Compilation

### General (Level 2)
| Item | Source Files |
|------|-------------|
| How do I compile? | `src/unifyweaver/core/compiler_driver.pl`, `docs/EXTENDED_README.md` |
| Implementation paradigms | `README.md` (Compilation Approaches table) |

### Targets (Level 3)
| Target | Source Files |
|--------|-------------|
| bash | `education/book-02-bash-target/`, `src/unifyweaver/targets/bash/` |
| go | `education/book-06-go-target/`, `src/unifyweaver/targets/go/` |
| rust | `education/book-09-rust-target/`, `src/unifyweaver/targets/rust/` |
| sql | `education/book-10-sql-target/`, `src/unifyweaver/targets/sql/` |
| python | `education/book-05-python-target/`, `src/unifyweaver/targets/python/` |
| csharp | `education/book-03-csharp-target/`, `src/unifyweaver/targets/csharp/` |
| powershell | `education/book-12-powershell-target/`, `src/unifyweaver/targets/powershell/` |
| prolog | `education/book-11-prolog-target/`, `src/unifyweaver/targets/prolog/` |

### Recursion Patterns (Level 3)
| Pattern | Source Files |
|---------|-------------|
| Linear/Tail/Tree | `docs/ADVANCED_RECURSION.md` |
| Transitive closure | `docs/ADVANCED_RECURSION.md`, `education/book-02-bash-target/` |
| Mutual recursion | `docs/ADVANCED_RECURSION.md` |

### Data (Level 3)
| Item | Source Files |
|------|-------------|
| JSON input | `docs/DATA_SOURCES_IMPLEMENTATION_PLAN.md` |
| Databases | `src/unifyweaver/sources/` |
| Aggregation | `docs/EXTENDED_README.md` |

---

## Mindmap

### General (Level 2)
| Item | Source Files |
|------|-------------|
| What are mindmap tools? | `scripts/mindmap/README.md` |

### Specific Tasks (Level 3)
| Task | Source Files |
|------|-------------|
| Link to Pearltrees | `scripts/mindmap/link_pearltrees.py`, `docs/QUICKSTART_MINDMAP_LINKING.md`, `skills/skill_mindmap_linking.md` |
| MST folder grouping | `scripts/mindmap/mst_folder_grouping.py`, `skills/skill_mst_folder_grouping.md` |
| Cross-references | `scripts/mindmap/add_relative_links.py`, `scripts/mindmap/build_index.py`, `skills/skill_mindmap_cross_links.md` |
| Folder suggestion | `scripts/mindmap/suggest_folder.py`, `skills/skill_folder_suggestion.md` |
| Rename mindmap | `scripts/mindmap/rename_mindmap.py` |

### Index Formats (Level 4)
| Format | Source Files |
|--------|-------------|
| JSON/TSV/SQLite | `scripts/mindmap/index_store.py` |

---

## Semantic Search

### General (Level 2)
| Item | Source Files |
|------|-------------|
| How does it work? | `docs/design/FEDERATED_MODEL_FORMAT.md` |

### Approaches (Level 3)
| Approach | Source Files |
|----------|-------------|
| Procrustes projection | `scripts/train_pearltrees_federated.py`, `docs/design/FEDERATED_MODEL_FORMAT.md` |
| Embedding models | `scripts/train_pearltrees_federated.py --help` |

### Training (Level 3)
| Item | Source Files |
|------|-------------|
| Train federated model | `scripts/train_pearltrees_federated.py`, `docs/QUICKSTART_MINDMAP_LINKING.md` |
| Clustering methods | `scripts/mindmap/hierarchy_objective.py` |

### Inference (Level 3)
| Item | Source Files |
|------|-------------|
| Run inference | `scripts/infer_pearltrees_federated.py` |
| Bookmark filing | `scripts/bookmark_filing_assistant.py`, `skills/skill_bookmark_filing.md` |

### Hierarchy Objectives (Level 3)
| Item | Source Files |
|------|-------------|
| J = D/(1+H) | `scripts/mindmap/hierarchy_objective.py` |
| Entropy sources | `scripts/mindmap/hierarchy_objective.py` (Fisher, BERT, modernBERT) |

---

## GUI

### General (Level 2)
| Item | Source Files |
|------|-------------|
| App generation overview | `education/other-books/book-gui-generation/README.md` |

### Frontend Targets (Level 3)
| Target | Source Files |
|--------|-------------|
| Vue 3 | `education/other-books/book-gui-generation/02_app_generation.md`, `src/unifyweaver/glue/app_generator.pl` |
| React Native | `education/other-books/book-gui-generation/02_app_generation.md` |
| Flutter | `education/other-books/book-gui-generation/02_app_generation.md` |
| SwiftUI | `education/other-books/book-gui-generation/02_app_generation.md` |

### Features (Level 3)
| Feature | Source Files |
|---------|-------------|
| Component library | `education/other-books/book-gui-generation/03_component_library.md` |
| Layout system | `education/other-books/book-gui-generation/04_layout_system.md` |
| Data binding | `education/other-books/book-gui-generation/05_data_binding.md` |
| Accessibility | `education/other-books/book-gui-generation/06_accessibility.md` |
| Responsive design | `education/other-books/book-gui-generation/07_responsive_design.md` |
| Theming | `education/other-books/book-gui-generation/08_theming.md` |

### Visualization Tools (Level 3)
| Tool | Source Files |
|------|-------------|
| Density explorer | `tools/density_explorer/` |

---

## Security

### Policy/Firewall (Level 2-3)
| Item | Source Files |
|------|-------------|
| Firewall overview | `docs/FIREWALL_GUIDE.md`, `education/book-08-security-firewall/` |
| Network policies | `docs/FIREWALL_GUIDE.md` |
| Service restrictions | `docs/CONTROL_PLANE.md` |

### Webapp Security (Level 2-3)
| Item | Source Files |
|------|-------------|
| Overview | `pr_shell_sandbox.md` |
| Navigation guards | `src/unifyweaver/glue/app_generator.pl`, `pr_shell_sandbox.md` |
| Auth backends | `src/unifyweaver/glue/auth_backends.pl`, `pr_shell_sandbox.md` |
| TLS config | `src/unifyweaver/glue/tls_config.pl`, `pr_shell_sandbox.md` |
| Shell sandbox | `src/unifyweaver/glue/shell_sandbox.pl`, `pr_shell_sandbox.md` |

---

## Generation Instructions

For each topic section, generate 3-5 Q&A pairs:

```jsonl
{
  "id": "unique_id",
  "question": "User-centric question",
  "question_variants": ["alt phrasing 1", "alt phrasing 2"],
  "level": 2 or 3,
  "tree_path": ["Branch", "Subbranch"],
  "answer": "Concise answer with code examples if relevant",
  "related_skills": ["skill_file.md"],
  "related_docs": ["doc_path.md"],
  "tags": ["topic1", "topic2"]
}
```

Questions should be what a new user would actually ask, not system-centric descriptions.
