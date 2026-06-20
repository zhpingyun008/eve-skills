#!/usr/bin/env python3
"""
AI Agent Skills Scanner
Extracts metadata from all ~/.hermes/skills/ SKILL.md files into a structured JSON dataset.
Handles both flat (SKILL.md at top) and nested (subdirectories with SKILL.md) layouts.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "skills.json")
STATS_FILE = os.path.join(OUTPUT_DIR, "stats.json")

EXCLUDED_DIRS = {"_archive", "_shared", "__pycache__", ".git"}


def parse_frontmatter(content: str) -> dict:
    """Parse YAML-like frontmatter from SKILL.md content."""
    meta = {}
    content_body = content

    # Match frontmatter between --- markers
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if m:
        frontmatter = m.group(1)
        content_body = content[m.end():].strip()

        # Parse simple key-value pairs and list values
        current_key = None
        list_key = None
        in_list = False

        for line in frontmatter.split('\n'):
            # Check for list continuation (indented with -)
            list_match = re.match(r'^\s+[-]\s+(.*)', line)
            if in_list and list_match and list_key:
                meta.setdefault(list_key, []).append(list_match.group(1).strip().strip('"').strip("'"))
                continue
            else:
                in_list = False
                list_key = None

            # Check for pipe block continuation
            pipe_match = re.match(r'^\s{2,}(\|.*)', line)
            if current_key and pipe_match:
                if isinstance(meta.get(current_key), str):
                    meta[current_key] += '\n' + pipe_match.group(1)
                continue

            # Key: value
            kv = re.match(r'^(\w[\w_-]*)\s*:\s*(.*)', line)
            if kv:
                current_key = kv.group(1)
                raw_value = kv.group(2).strip()
                if raw_value == '':
                    meta[current_key] = ''
                elif raw_value.startswith('"') and raw_value.endswith('"'):
                    meta[current_key] = raw_value[1:-1]
                elif raw_value.startswith("'") and raw_value.endswith("'"):
                    meta[current_key] = raw_value[1:-1]
                elif raw_value.startswith('['):
                    # Inline list
                    try:
                        items = json.loads(raw_value)
                        meta[current_key] = items if isinstance(items, list) else [items]
                    except json.JSONDecodeError:
                        meta[current_key] = raw_value
                elif raw_value == 'true':
                    meta[current_key] = True
                elif raw_value == 'false':
                    meta[current_key] = False
                elif raw_value.startswith('|'):
                    # Start of pipe block
                    meta[current_key] = raw_value
                else:
                    meta[current_key] = raw_value

                # Check if next lines are a list
                in_list = False
                list_key = None
            else:
                current_key = None

    return meta, content_body


def get_category_from_path(skill_path: str) -> str:
    """Determine the category from the path structure."""
    rel = os.path.relpath(skill_path, SKILLS_DIR)
    parts = rel.split(os.sep)
    if len(parts) >= 2:
        return parts[0]
    return "uncategorized"


def get_skill_id(name: str, category: str) -> str:
    """Create a unique skill ID."""
    return f"{category}/{name}" if category != "uncategorized" else name


def get_skill_level(path: str) -> int:
    """Determine if this is a category-level (1) or sub-skill (2)."""
    rel = os.path.relpath(path, SKILLS_DIR)
    parts = rel.split(os.sep)
    return len(parts)


def extract_file_list(skill_dir: str) -> list:
    """List all files in the skill directory (relative paths)."""
    files = []
    for root, dirs, fnames in os.walk(skill_dir):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fname in fnames:
            if fname.startswith('.'):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, skill_dir)
            fsize = os.path.getsize(full_path)
            files.append({
                "path": rel_path,
                "size_bytes": fsize,
                "ext": os.path.splitext(fname)[1].lower()
            })
    return sorted(files, key=lambda x: x["path"])


def calculate_file_size(skill_dir: str) -> int:
    """Calculate total size of files in the skill directory."""
    total = 0
    for root, dirs, fnames in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fname in fnames:
            if fname.startswith('.'):
                continue
            total += os.path.getsize(os.path.join(root, fname))
    return total


def scan_skills() -> list:
    """Scan all skills and extract metadata."""
    skills = []
    errors = []

    # First pass: find all SKILL.md files
    skill_files = []
    for root, dirs, fnames in os.walk(SKILLS_DIR):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if 'SKILL.md' in fnames:
            skill_files.append(os.path.join(root, 'SKILL.md'))

    print(f"Found {len(skill_files)} SKILL.md files")

    for sf_path in sorted(skill_files):
        skill_dir = os.path.dirname(sf_path)
        rel_dir = os.path.relpath(skill_dir, SKILLS_DIR)
        category = get_category_from_path(sf_path)
        level = get_skill_level(sf_path)

        try:
            with open(sf_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            meta, content_body = parse_frontmatter(content)

            # Build skill record
            skill_name = meta.get('name', os.path.basename(skill_dir))
            skill_id = get_skill_id(skill_name, category)

            description = meta.get('description', '')
            if not description:
                # Extract first non-empty line from content body
                for line in content_body.split('\n'):
                    line = line.strip().strip('#').strip()
                    if line and len(line) > 10:
                        description = line[:200]
                        break

            triggers = meta.get('triggers', meta.get('trigger', []))
            if isinstance(triggers, str):
                triggers = [triggers]

            record = {
                "id": skill_id,
                "name": skill_name,
                "slug": skill_name.lower().replace(' ', '-'),
                "description": description[:500] if description else "",
                "category": category,
                "version": meta.get('version', '1.0.0'),
                "author": meta.get('author', 'Unknown'),
                "triggers": triggers if isinstance(triggers, list) else [triggers] if triggers else [],
                "depends_on": meta.get('depends_on', []),
                "depends_on_raw": str(meta.get('depends_on', '')),
                "related_skills": meta.get('related_skills', []),
                "permanent": meta.get('permanent', False),
                "locked": meta.get('locked', False),
                "tags": meta.get('tags', []),
                "level": level,
                "path": rel_dir,
                "skill_dir": skill_dir,
                "content_length": len(content),
                "content_preview": content_body[:300] if content_body else "",
                "files": extract_file_list(skill_dir),
                "file_count": len(extract_file_list(skill_dir)),
                "total_size_bytes": calculate_file_size(skill_dir),
                "has_readme": any(f['path'] == 'README.md' for f in extract_file_list(skill_dir) if 'path' in f),
                "scripts_count": sum(1 for f in extract_file_list(skill_dir) if f.get('path', '').startswith('scripts/')),
                "scanned_at": datetime.utcnow().isoformat()
            }

            skills.append(record)

        except Exception as e:
            errors.append({"file": sf_path, "error": str(e)})
            print(f"  ERROR scanning {sf_path}: {e}")

    return skills, errors


def compute_stats(skills: list) -> dict:
    """Compute statistics about the skill dataset."""
    categories = {}
    for s in skills:
        cat = s['category']
        categories.setdefault(cat, {"count": 0, "skills": []})
        categories[cat]["count"] += 1
        categories[cat]["skills"].append(s['name'])

    total_file_count = sum(s['file_count'] for s in skills)
    total_size = sum(s['total_size_bytes'] for s in skills)

    return {
        "total_skills": len(skills),
        "total_categories": len(categories),
        "total_files": total_file_count,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "categories": {k: v["count"] for k, v in sorted(categories.items(), key=lambda x: -x[1]["count"])},
        "avg_files_per_skill": round(total_file_count / len(skills), 1) if skills else 0,
        "scanned_at": datetime.utcnow().isoformat()
    }


def main():
    print("=" * 60)
    print("AI Agent Skills Scanner")
    print(f"Scanning: {SKILLS_DIR}")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    skills, errors = scan_skills()
    stats = compute_stats(skills)

    # Write skills JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Skills written to {OUTPUT_FILE}")
    print(f"  {len(skills)} skills")

    # Write stats JSON
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✓ Stats written to {STATS_FILE}")

    print(f"\n📊 Statistics:")
    for k, v in stats.items():
        if k == 'categories':
            print(f"\n  Categories ({len(v)}):")
            for cat, count in sorted(v.items(), key=lambda x: -x[1]):
                print(f"    {cat}: {count}")
        elif k != 'scanned_at' and not isinstance(v, dict):
            print(f"  {k}: {v}")

    if errors:
        print(f"\n⚠ {len(errors)} scan errors:")
        for e in errors[:5]:
            print(f"  - {e['file']}: {e['error']}")

    print("\n✅ Scan complete!")


if __name__ == "__main__":
    main()
