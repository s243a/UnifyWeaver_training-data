#!/usr/bin/env python3
"""
Generate quickstart Q&A entries from skills documents.

Skills already contain:
- "When to Use" sections → natural questions
- Commands and examples → answers
- Related docs/code references → related_docs field

Usage:
    python scripts/generate_qa_from_skills.py --skill skill_mindmap_linking.md
    python scripts/generate_qa_from_skills.py --all --model haiku
    python scripts/generate_qa_from_skills.py --all --provider gemini
"""

import argparse
import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional


# Base path to UnifyWeaver project
# training-data/scripts/ -> training-data/ -> UnifyWeaver/
UNIFYWEAVER_BASE = Path(__file__).parent.parent.parent
SKILLS_DIR = UNIFYWEAVER_BASE / "skills"

# If running from training-data subdir, adjust path
if not SKILLS_DIR.exists():
    # Try absolute path
    UNIFYWEAVER_BASE = Path("/home/s243a/Projects/UnifyWeaver")
    SKILLS_DIR = UNIFYWEAVER_BASE / "skills"


GENERATION_PROMPT = '''You are generating Q&A training data for UnifyWeaver's quickstart agent.

Given this SKILL document, generate {num_pairs} Q&A pairs.

SKILL FILE: {skill_file}

SKILL CONTENT:
{skill_content}

Generate Q&A pairs that:
1. Questions should be what a NEW USER would ask (based on "When to Use" section)
2. Answers should be concise, pointing to this skill and its commands
3. Include the skill file in related_skills
4. Include any docs/code mentioned in "Related" section in related_docs

Output format (JSONL, one per line):
{{"id": "{skill_id}_001", "question": "...", "question_variants": ["...", "..."], "level": 2, "tree_path": {tree_path}, "answer": "...", "related_skills": ["{skill_file}"], "related_docs": [...], "tags": [...]}}

IMPORTANT:
- Level 2 = general task ("How do I organize mindmaps?")
- Level 3 = specific task ("How do I use MST clustering?")
- Questions should NOT mention the skill name - users don't know skill names!

Generate ONLY the JSONL output, no explanations.'''


def call_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 120) -> Optional[str]:
    """Call claude CLI."""
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
    """Call gemini CLI."""
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


def infer_topic_from_skill(skill_name: str) -> str:
    """Infer the topic folder from skill filename."""
    if 'mindmap' in skill_name or 'mst' in skill_name or 'folder' in skill_name:
        return 'mindmap'
    elif 'bookmark' in skill_name:
        return 'semantic-search'  # bookmark filing uses semantic search
    elif 'compile' in skill_name or 'environment' in skill_name or 'executable' in skill_name:
        return 'compilation'
    elif 'json' in skill_name or 'extract' in skill_name:
        return 'compilation'  # data processing relates to compilation
    else:
        return 'quickstart'


def infer_tree_path(skill_name: str, skill_content: str) -> List[str]:
    """Infer tree path from skill name and content."""
    topic = infer_topic_from_skill(skill_name)

    # Extract skill title from content
    title_match = re.search(r'^# Skill: (.+)$', skill_content, re.MULTILINE)
    if title_match:
        subtopic = title_match.group(1)
    else:
        subtopic = skill_name.replace('skill_', '').replace('.md', '').replace('_', ' ').title()

    return [topic.title(), subtopic]


def generate_qa_from_skill(
    skill_path: Path,
    provider: str = "claude",
    model: str = "sonnet",
    num_pairs: int = 4
) -> List[Dict]:
    """Generate Q&A pairs from a skill file."""

    skill_content = skill_path.read_text()
    skill_name = skill_path.name
    skill_id = skill_name.replace('.md', '').replace('-', '_')

    tree_path = infer_tree_path(skill_name, skill_content)

    prompt = GENERATION_PROMPT.format(
        skill_file=skill_name,
        skill_content=skill_content,
        num_pairs=num_pairs,
        skill_id=skill_id,
        tree_path=json.dumps(tree_path)
    )

    print(f"  Generating from {skill_name}...")
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
                # Ensure skill is in related_skills
                if skill_name not in obj.get('related_skills', []):
                    obj.setdefault('related_skills', []).append(skill_name)
                results.append(obj)
            except json.JSONDecodeError:
                pass

    return results


def analyze_coverage() -> Dict[str, List[str]]:
    """Analyze skill coverage vs capability tree. Returns gaps."""

    # Capability tree items that should have skills
    capability_tree = {
        'compilation': [
            'compile prolog',
            'bash target',
            'go target',
            'python target',
            'sql target',
            'rust target',
            'csharp target',
            'powershell target',
            'recursion patterns',
            'data sources',
        ],
        'mindmap': [
            'link to pearltrees',
            'mst folder grouping',
            'cross-references',
            'folder suggestion',
            'rename mindmap',
            'build index',
        ],
        'semantic-search': [
            'train model',
            'inference',
            'bookmark filing',
            'folder suggestion',
        ],
        'gui': [
            'app generation',
            'vue target',
            'react native target',
            'flutter target',
            'component library',
            'theming',
            'density explorer',
        ],
        'security': [
            'firewall policies',
            'navigation guards',
            'auth backends',
            'tls config',
            'shell sandbox',
        ],
    }

    # Existing skills
    existing_skills = {}
    for skill_file in SKILLS_DIR.glob("skill_*.md"):
        content = skill_file.read_text().lower()
        name = skill_file.stem

        # Extract keywords from skill
        keywords = set()
        if 'mindmap' in name or 'mst' in name:
            keywords.add('mindmap')
        if 'link' in name:
            keywords.add('link to pearltrees')
        if 'mst' in name or 'folder_grouping' in name:
            keywords.add('mst folder grouping')
        if 'cross' in name or 'relative_link' in name:
            keywords.add('cross-references')
        if 'folder_suggestion' in name or 'suggest' in name:
            keywords.add('folder suggestion')
        if 'rename' in name:
            keywords.add('rename mindmap')
        if 'index' in name:
            keywords.add('build index')
        if 'bookmark' in name:
            keywords.add('bookmark filing')
        if 'compile' in name:
            keywords.add('compile prolog')
        if 'environment' in name:
            keywords.add('environment setup')
        if 'json' in name:
            keywords.add('data sources')
        if 'extract' in name:
            keywords.add('data extraction')

        existing_skills[name] = keywords

    # Find gaps
    gaps = {}
    all_covered = set()
    for skill_keywords in existing_skills.values():
        all_covered.update(skill_keywords)

    for topic, items in capability_tree.items():
        topic_gaps = []
        for item in items:
            # Check if item is covered by any skill
            covered = False
            for keyword in all_covered:
                if item in keyword or keyword in item:
                    covered = True
                    break
            if not covered:
                topic_gaps.append(item)

        if topic_gaps:
            gaps[topic] = topic_gaps

    return gaps


def print_coverage_report():
    """Print coverage analysis report."""
    print("\n=== SKILL COVERAGE ANALYSIS ===\n")

    print("Existing skills:")
    for skill_file in sorted(SKILLS_DIR.glob("skill_*.md")):
        print(f"  ✓ {skill_file.name}")

    gaps = analyze_coverage()

    if gaps:
        print("\n⚠️  Missing skills (capability tree items without skills):\n")
        for topic, items in gaps.items():
            print(f"  {topic.upper()}:")
            for item in items:
                print(f"    - {item}")

        print("\n💡 Suggested new skills to create:")
        for topic, items in gaps.items():
            for item in items:
                skill_name = f"skill_{item.replace(' ', '_').replace('-', '_')}.md"
                print(f"    skills/{skill_name}")
    else:
        print("\n✓ All capability tree items have skills!")

    print()


def main():
    parser = argparse.ArgumentParser(description="Generate Q&A from skills documents")
    parser.add_argument("--skill", help="Process specific skill file")
    parser.add_argument("--all", action="store_true", help="Process all skills")
    parser.add_argument("--coverage", action="store_true", help="Analyze skill coverage gaps")
    parser.add_argument("--provider", default="claude", choices=["claude", "gemini"])
    parser.add_argument("--model", default="sonnet", help="Model to use")
    parser.add_argument("--pairs", type=int, default=4, help="Q&A pairs per skill")
    parser.add_argument("--output", type=Path, default=Path("by-topic"), help="Output directory")

    args = parser.parse_args()

    if args.coverage:
        print_coverage_report()
        return

    if not SKILLS_DIR.exists():
        print(f"Error: Skills directory not found: {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    if args.skill:
        skill_files = [SKILLS_DIR / args.skill]
    elif args.all:
        skill_files = sorted(SKILLS_DIR.glob("skill_*.md"))
    else:
        print("Specify --skill <filename> or --all")
        print(f"Available skills:")
        for f in sorted(SKILLS_DIR.glob("skill_*.md")):
            print(f"  {f.name}")
        sys.exit(1)

    # Group results by topic
    results_by_topic: Dict[str, List[Dict]] = {}

    for skill_path in skill_files:
        if not skill_path.exists():
            print(f"Skill not found: {skill_path}")
            continue

        pairs = generate_qa_from_skill(
            skill_path,
            provider=args.provider,
            model=args.model,
            num_pairs=args.pairs
        )

        topic = infer_topic_from_skill(skill_path.name)
        results_by_topic.setdefault(topic, []).extend(pairs)

        print(f"    Generated {len(pairs)} pairs → {topic}/")

    # Write output files
    for topic, pairs in results_by_topic.items():
        if not pairs:
            continue

        output_dir = args.output / topic
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "skills-generated.jsonl"

        # Append to existing or create new
        mode = 'a' if output_file.exists() else 'w'
        with open(output_file, mode) as f:
            for pair in pairs:
                f.write(json.dumps(pair) + '\n')

        print(f"\nWrote {len(pairs)} pairs to {output_file}")


if __name__ == "__main__":
    main()
