#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# Copyright (c) 2025 John William Creighton (s243a)
#
# Import Training Data to Unified KG Database

"""
Import JSONL training data files into the unified KG topology database.

Reads from:
    training-data/education/
    training-data/source/
    training-data/playbooks/
    training-data/docs/
    training-data/prerequisites/

Outputs:
    training-data/unified.db
    training-data/embeddings/

Usage:
    python import_training_data.py --input training-data/ --output training-data/unified.db
    python import_training_data.py --input training-data/ --dry-run
    python import_training_data.py --input training-data/ --model all-MiniLM-L6-v2
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'unifyweaver' / 'targets' / 'python_runtime'))

try:
    from kg_topology_api import KGTopologyAPI, ALL_RELATION_TYPES
except ImportError:
    print("Error: Could not import kg_topology_api. Make sure you're running from the project root.")
    print("Try: cd UnifyWeaver && python training-data/scripts/import_training_data.py")
    sys.exit(1)


def iter_jsonl_files(base_dir: Path) -> Iterator[Path]:
    """Iterate over all JSONL files in the training data directory."""
    # Fixed subdirectories
    for subdir in ['education', 'source', 'playbooks', 'docs', 'prerequisites']:
        subdir_path = base_dir / subdir
        if subdir_path.exists():
            for jsonl_file in subdir_path.rglob('*.jsonl'):
                yield jsonl_file

    # Also scan book-* directories (e.g., book-01-foundations)
    for subdir_path in base_dir.iterdir():
        if subdir_path.is_dir() and subdir_path.name.startswith('book-'):
            for jsonl_file in subdir_path.rglob('*.jsonl'):
                yield jsonl_file


def parse_jsonl(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Parse a JSONL file, yielding each record."""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  Warning: JSON error in {file_path}:{line_num}: {e}")


def infer_source_type(source_file: str) -> str:
    """Infer source_type from file path string."""
    parts = Path(source_file).parts
    if parts and parts[0] in ['education', 'source', 'playbooks', 'docs', 'prerequisites']:
        return parts[0]
    if parts and parts[0].startswith('book-'):
        return 'education'
    return 'unknown'


class TrainingDataImporter:
    """Import training data into KG topology database."""

    def __init__(self, db_path: str, embeddings_dir: str, model_name: str = 'all-MiniLM-L6-v2'):
        self.db_path = db_path
        self.embeddings_dir = embeddings_dir
        self.model_name = model_name
        self.db: Optional[KGTopologyAPI] = None
        self.model_id: Optional[int] = None

        # Track what we've imported
        self.stats = {
            'files_processed': 0,
            'clusters_created': 0,
            'answers_created': 0,
            'questions_created': 0,
            'relations_created': 0,
            'interfaces_created': 0,
            'errors': 0
        }

        # Map cluster_id strings to database IDs
        self.cluster_id_map: Dict[str, int] = {}
        self.answer_id_map: Dict[str, int] = {}

    def connect(self):
        """Connect to the database."""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        os.makedirs(self.embeddings_dir, exist_ok=True)

        self.db = KGTopologyAPI(self.db_path, self.embeddings_dir)

        # Get or create embedding model
        # Note: Actual embedding requires sentence-transformers or similar
        # For now, we just register the model
        self.model_id = self._get_or_create_model()

        print(f"Connected to database: {self.db_path}")
        print(f"Embeddings directory: {self.embeddings_dir}")
        print(f"Model: {self.model_name} (ID: {self.model_id})")

    def _get_or_create_model(self) -> int:
        """Get or create embedding model record."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT model_id FROM embedding_models WHERE name = ?", (self.model_name,))
        row = cursor.fetchone()
        if row:
            return row['model_id']

        # Create new model record
        # Dimension depends on model - all-MiniLM-L6-v2 is 384
        dimensions = {
            'all-MiniLM-L6-v2': 384,
            'all-mpnet-base-v2': 768,
            'nomic-embed-text-v1.5': 768,
        }.get(self.model_name, 384)

        cursor.execute("""
            INSERT INTO embedding_models (name, dimension, backend, notes)
            VALUES (?, ?, 'sentence-transformers', 'Created by import_training_data.py')
        """, (self.model_name, dimensions))
        self.db.conn.commit()
        return cursor.lastrowid

    def import_cluster(self, record: Dict[str, Any], source_file: str) -> Optional[int]:
        """Import a single cluster record."""
        cluster_id_str = record.get('cluster_id', '')
        if not cluster_id_str:
            print(f"  Warning: Record missing cluster_id in {source_file}")
            return None

        # Extract answer content
        answer_data = record.get('answer', {})
        answer_text = answer_data.get('text', '')

        # Include code blocks in answer text for embedding
        code_blocks = answer_data.get('code_blocks', [])
        for block in code_blocks:
            if block.get('code'):
                answer_text += f"\n\n```{block.get('language', '')}\n{block['code']}\n```"

        if not answer_text:
            print(f"  Warning: Empty answer for {cluster_id_str}")
            return None

        # Create cluster
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO qa_clusters (name, description)
            VALUES (?, ?)
        """, (cluster_id_str, record.get('section', '')))
        db_cluster_id = cursor.lastrowid
        self.stats['clusters_created'] += 1

        # Create answer
        source_type = record.get('source_type', infer_source_type(source_file))
        cursor.execute("""
            INSERT INTO answers (source_file, record_id, text, text_variant)
            VALUES (?, ?, ?, 'default')
        """, (record.get('source_file', source_file), cluster_id_str, answer_text))
        db_answer_id = cursor.lastrowid
        self.stats['answers_created'] += 1

        # Link answer to cluster
        cursor.execute("""
            INSERT INTO cluster_answers (cluster_id, answer_id)
            VALUES (?, ?)
        """, (db_cluster_id, db_answer_id))

        # Create questions
        questions = record.get('questions', [])
        for q in questions:
            q_text = q.get('text', q) if isinstance(q, dict) else q
            if q_text:
                length_type = q.get('length', 'short') if isinstance(q, dict) else 'short'
                cursor.execute("""
                    INSERT INTO questions (text, length_type)
                    VALUES (?, ?)
                """, (q_text, length_type))
                q_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO cluster_questions (cluster_id, question_id)
                    VALUES (?, ?)
                """, (db_cluster_id, q_id))
                self.stats['questions_created'] += 1

        self.db.conn.commit()

        # Track mapping
        self.cluster_id_map[cluster_id_str] = db_cluster_id
        self.answer_id_map[cluster_id_str] = db_answer_id

        return db_cluster_id

    def import_relations(self, record: Dict[str, Any]):
        """Import relations from a cluster record."""
        cluster_id_str = record.get('cluster_id', '')
        relations = record.get('relations', [])

        from_answer_id = self.answer_id_map.get(cluster_id_str)
        if not from_answer_id:
            return

        for rel in relations:
            to_cluster = rel.get('to', '')
            rel_type = rel.get('type', '')

            if rel_type not in ALL_RELATION_TYPES:
                print(f"  Warning: Unknown relation type '{rel_type}' in {cluster_id_str}")
                continue

            to_answer_id = self.answer_id_map.get(to_cluster)
            if not to_answer_id:
                # Target not yet imported - store for later
                continue

            try:
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO answer_relations (from_answer_id, to_answer_id, relation_type, metadata)
                    VALUES (?, ?, ?, ?)
                """, (from_answer_id, to_answer_id, rel_type, json.dumps(rel.get('metadata', {}))))
                if cursor.rowcount > 0:
                    self.stats['relations_created'] += 1
            except Exception as e:
                print(f"  Warning: Could not create relation: {e}")

        self.db.conn.commit()

    def create_interfaces_from_structure(self, base_dir: Path):
        """Create semantic interfaces based on folder structure."""
        interfaces_to_create = set()

        # Collect interface names from folder structure
        for subdir in ['education', 'source', 'playbooks', 'docs', 'prerequisites']:
            subdir_path = base_dir / subdir
            if not subdir_path.exists():
                continue

            # Top-level interface for each category
            interfaces_to_create.add(subdir)

            # Sub-interfaces for education books
            if subdir == 'education':
                for book_dir in subdir_path.iterdir():
                    if book_dir.is_dir() and book_dir.name.startswith('book-'):
                        interfaces_to_create.add(book_dir.name)

            # Sub-interfaces for source modules
            if subdir == 'source':
                for module_dir in subdir_path.iterdir():
                    if module_dir.is_dir():
                        interfaces_to_create.add(f"source-{module_dir.name}")

        # Create interfaces
        for interface_name in sorted(interfaces_to_create):
            try:
                self.db.create_interface(
                    name=interface_name,
                    description=f"Auto-generated interface for {interface_name}",
                    topics=[]
                )
                self.stats['interfaces_created'] += 1
                print(f"  Created interface: {interface_name}")
            except Exception as e:
                # Interface may already exist
                pass

    def assign_clusters_to_interfaces(self):
        """Assign clusters to their appropriate interfaces based on source_file."""
        cursor = self.db.conn.cursor()

        for cluster_id_str, db_cluster_id in self.cluster_id_map.items():
            # Determine interface from cluster_id pattern
            interface_name = None

            if cluster_id_str.startswith('book-'):
                # Education: book-01-ch02-facts -> book-01-foundations
                parts = cluster_id_str.split('-')
                if len(parts) >= 2:
                    interface_name = f"{parts[0]}-{parts[1]}"
            elif cluster_id_str.startswith('prereq-'):
                interface_name = 'prerequisites'
            elif '_target-' in cluster_id_str or cluster_id_str.endswith('_target'):
                interface_name = 'source-targets'
            elif cluster_id_str.startswith('playbook-'):
                interface_name = 'playbooks'

            if interface_name:
                interface = self.db.get_interface_by_name(interface_name)
                if interface:
                    try:
                        self.db.add_interface_cluster(interface['interface_id'], db_cluster_id)
                    except Exception:
                        pass  # May already be assigned

    def import_all(self, base_dir: Path, dry_run: bool = False):
        """Import all training data from the base directory."""
        if dry_run:
            print("DRY RUN - No changes will be made\n")

        print(f"Scanning {base_dir} for JSONL files...\n")

        # First pass: collect all records
        all_records = []
        for jsonl_file in iter_jsonl_files(base_dir):
            relative_path = jsonl_file.relative_to(base_dir)
            print(f"Reading: {relative_path}")

            for record in parse_jsonl(jsonl_file):
                record['_source_file'] = str(relative_path)
                all_records.append(record)

            self.stats['files_processed'] += 1

        print(f"\nFound {len(all_records)} records in {self.stats['files_processed']} files\n")

        if dry_run:
            print("Would create:")
            print(f"  - {len(all_records)} clusters")
            print(f"  - {sum(len(r.get('questions', [])) for r in all_records)} questions")
            print(f"  - {sum(len(r.get('relations', [])) for r in all_records)} relations")
            return

        # Connect and import
        self.connect()

        # Import clusters
        print("Importing clusters...")
        for record in all_records:
            try:
                self.import_cluster(record, record['_source_file'])
            except Exception as e:
                print(f"  Error importing {record.get('cluster_id', 'unknown')}: {e}")
                self.stats['errors'] += 1

        # Import relations (second pass, after all clusters exist)
        print("\nImporting relations...")
        for record in all_records:
            try:
                self.import_relations(record)
            except Exception as e:
                print(f"  Error importing relations for {record.get('cluster_id', 'unknown')}: {e}")

        # Create interfaces
        print("\nCreating semantic interfaces...")
        self.create_interfaces_from_structure(base_dir)

        # Assign clusters to interfaces
        print("Assigning clusters to interfaces...")
        self.assign_clusters_to_interfaces()

        # Print summary
        print("\n" + "=" * 50)
        print("Import Summary")
        print("=" * 50)
        for key, value in self.stats.items():
            print(f"  {key}: {value}")

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Import training data into unified KG database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python import_training_data.py --input training-data/
  python import_training_data.py --input training-data/ --dry-run
  python import_training_data.py --input training-data/ --model nomic-embed-text-v1.5
        """
    )
    parser.add_argument('--input', '-i', required=True, help='Training data directory')
    parser.add_argument('--output', '-o', help='Output database path (default: INPUT/unified.db)')
    parser.add_argument('--embeddings', '-e', help='Embeddings directory (default: INPUT/embeddings)')
    parser.add_argument('--model', '-m', default='all-MiniLM-L6-v2', help='Embedding model name')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be imported')

    args = parser.parse_args()

    base_dir = Path(args.input)
    if not base_dir.exists():
        print(f"Error: Input directory not found: {base_dir}")
        sys.exit(1)

    db_path = args.output or str(base_dir / 'unified.db')
    embeddings_dir = args.embeddings or str(base_dir / 'embeddings')

    importer = TrainingDataImporter(db_path, embeddings_dir, args.model)

    try:
        importer.import_all(base_dir, dry_run=args.dry_run)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
