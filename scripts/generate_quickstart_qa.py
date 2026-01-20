#!/usr/bin/env python3
"""
Generate quickstart Q&A entries from source files.

Reads SOURCE_MAPPING.md and generates Q&A pairs for each topic
by having an LLM read the relevant source files.

Usage:
    python scripts/generate_quickstart_qa.py --topic compilation
    python scripts/generate_quickstart_qa.py --topic mindmap --model haiku
    python scripts/generate_quickstart_qa.py --all --provider gemini
"""

import argparse
import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


# Base path to UnifyWeaver project
UNIFYWEAVER_BASE = Path(__file__).parent.parent.parent  # training-data/../ = UnifyWeaver


GENERATION_PROMPT = '''You are generating Q&A training data for UnifyWeaver's quickstart agent.

TOPIC: {topic}
LEVEL: {level} ({level_desc})

SOURCE FILES TO REFERENCE:
{source_files}

SOURCE CONTENT:
{source_content}

Generate {num_pairs} Q&A pairs for this topic. Each pair should:
1. Ask a question a NEW USER would actually ask (user-centric, not system-centric)
2. Answer concisely with accurate technical information from the sources
3. Include code examples where helpful
4. Reference paths for "learn more" (e.g., "See education/book-02-bash-target/")

Output as JSONL (one JSON object per line):
{{"id": "{topic_id}_001", "question": "...", "question_variants": ["...", "..."], "level": {level}, "tree_path": {tree_path}, "answer": "...", "related_skills": [...], "related_docs": [...], "tags": [...]}}

Generate ONLY the JSONL output, no explanations.'''


def call_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 120) -> Optional[str]:
    """Call claude CLI with the given prompt."""
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"CLI error: {result.stderr[:200]}", file=sys.stderr)
            return None
    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Exception: {e}", file=sys.stderr)
        return None


def call_gemini_cli(prompt: str, model: str = "gemini-2.5-flash-preview-05-20", timeout: int = 120) -> Optional[str]:
    """Call gemini CLI with the given prompt."""
    try:
        result = subprocess.run(
            ["gemini", "-p", prompt, "-m", model, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Gemini CLI error: {result.stderr[:200]}", file=sys.stderr)
            return None
    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Exception: {e}", file=sys.stderr)
        return None


def call_llm(prompt: str, provider: str = "claude", model: str = "sonnet") -> Optional[str]:
    """Call LLM based on provider."""
    if provider == "gemini":
        return call_gemini_cli(prompt, model)
    else:
        return call_claude_cli(prompt, model)


def read_source_file(path: str, max_lines: int = 200) -> str:
    """Read a source file, truncating if too long."""
    full_path = UNIFYWEAVER_BASE / path

    if full_path.is_dir():
        # Read README if directory
        readme = full_path / "README.md"
        if readme.exists():
            full_path = readme
        else:
            # List files in directory
            files = list(full_path.glob("*.md")) + list(full_path.glob("*.py")) + list(full_path.glob("*.pl"))
            return f"Directory {path} contains: {[f.name for f in files[:10]]}"

    if not full_path.exists():
        return f"[File not found: {path}]"

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                content = ''.join(lines[:max_lines])
                content += f"\n... [truncated, {len(lines) - max_lines} more lines]"
                return content
            return ''.join(lines)
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def parse_source_mapping(mapping_path: Path) -> Dict[str, Dict]:
    """Parse SOURCE_MAPPING.md into structured data."""
    content = mapping_path.read_text()

    topics = {}
    current_topic = None
    current_section = None

    for line in content.split('\n'):
        # Main topic headers
        if line.startswith('## ') and not line.startswith('## How'):
            current_topic = line[3:].strip().lower().replace(' ', '-')
            topics[current_topic] = {'sections': {}}

        # Section headers
        elif line.startswith('### ') and current_topic:
            section_match = re.match(r'### (.+?) \(Level (\d+)(?:-(\d+))?\)', line)
            if section_match:
                section_name = section_match.group(1).lower().replace(' ', '-')
                level = int(section_match.group(2))
                current_section = section_name
                topics[current_topic]['sections'][current_section] = {
                    'level': level,
                    'items': []
                }

        # Table rows with source files
        elif line.startswith('|') and current_topic and current_section:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2 and parts[0] and not parts[0].startswith('-'):
                item_name = parts[0]
                source_files = [s.strip().strip('`') for s in parts[1].split(',')]
                if item_name.lower() not in ['item', 'target', 'pattern', 'task', 'feature', 'tool', 'format', 'approach']:
                    topics[current_topic]['sections'][current_section]['items'].append({
                        'name': item_name,
                        'sources': source_files
                    })

    return topics


def generate_qa_for_section(
    topic: str,
    section: str,
    section_data: Dict,
    provider: str = "claude",
    model: str = "sonnet",
    num_pairs: int = 3
) -> List[Dict]:
    """Generate Q&A pairs for a section."""

    # Collect all source files for this section
    all_sources = []
    for item in section_data['items']:
        all_sources.extend(item['sources'])
    all_sources = list(set(all_sources))

    # Read source content
    source_content = ""
    for src in all_sources[:5]:  # Limit to 5 files
        content = read_source_file(src, max_lines=150)
        source_content += f"\n\n=== {src} ===\n{content}"

    if len(source_content) > 15000:
        source_content = source_content[:15000] + "\n... [content truncated]"

    level = section_data['level']
    level_desc = {
        0: "identity",
        1: "capabilities",
        2: "general task",
        3: "specific task",
        4: "details"
    }.get(level, "task")

    tree_path = json.dumps([topic.title(), section.replace('-', ' ').title()])

    prompt = GENERATION_PROMPT.format(
        topic=f"{topic} / {section}",
        level=level,
        level_desc=level_desc,
        source_files='\n'.join(f"- {s}" for s in all_sources),
        source_content=source_content,
        num_pairs=num_pairs,
        topic_id=f"{topic}_{section}".replace('-', '_'),
        tree_path=tree_path
    )

    print(f"  Generating {num_pairs} pairs for {topic}/{section}...")
    response = call_llm(prompt, provider, model)

    if not response:
        return []

    # Parse JSONL response
    results = []
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                obj = json.loads(line)
                results.append(obj)
            except json.JSONDecodeError:
                pass

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate quickstart Q&A from source files")
    parser.add_argument("--topic", help="Generate for specific topic (compilation, mindmap, etc.)")
    parser.add_argument("--all", action="store_true", help="Generate for all topics")
    parser.add_argument("--provider", default="claude", choices=["claude", "gemini"])
    parser.add_argument("--model", default="sonnet", help="Model to use")
    parser.add_argument("--pairs", type=int, default=3, help="Q&A pairs per section")
    parser.add_argument("--output", type=Path, default=Path("by-topic"), help="Output directory")

    args = parser.parse_args()

    mapping_path = Path(__file__).parent.parent / "by-topic" / "SOURCE_MAPPING.md"
    if not mapping_path.exists():
        print(f"Error: {mapping_path} not found", file=sys.stderr)
        sys.exit(1)

    topics = parse_source_mapping(mapping_path)

    if args.topic:
        topics_to_process = {args.topic: topics.get(args.topic, {})}
    elif args.all:
        topics_to_process = topics
    else:
        print("Specify --topic or --all")
        print(f"Available topics: {list(topics.keys())}")
        sys.exit(1)

    for topic_name, topic_data in topics_to_process.items():
        if not topic_data or 'sections' not in topic_data:
            print(f"Skipping {topic_name}: no sections found")
            continue

        print(f"\n=== {topic_name.upper()} ===")

        all_pairs = []
        for section_name, section_data in topic_data['sections'].items():
            if not section_data.get('items'):
                continue

            pairs = generate_qa_for_section(
                topic_name, section_name, section_data,
                provider=args.provider,
                model=args.model,
                num_pairs=args.pairs
            )
            all_pairs.extend(pairs)
            print(f"    Generated {len(pairs)} pairs")

        if all_pairs:
            output_dir = args.output / topic_name
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{topic_name}-generated.jsonl"

            with open(output_file, 'w') as f:
                for pair in all_pairs:
                    f.write(json.dumps(pair) + '\n')

            print(f"  Wrote {len(all_pairs)} pairs to {output_file}")


if __name__ == "__main__":
    main()
