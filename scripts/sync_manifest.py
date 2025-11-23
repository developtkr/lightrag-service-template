import os
import sys
import argparse
import yaml
import logging

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_core import load_yaml, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def generate_doc_id(file_path: str) -> str:
    base_name = os.path.basename(file_path)
    return os.path.splitext(base_name)[0]

def get_all_files(kb_dir: str):
    supported_exts = {'.md', '.txt', '.pdf', '.docx', '.pptx'}
    all_files = []
    for root, _, files in os.walk(kb_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, kb_dir)
                all_files.append(rel_path)
    return all_files

def determine_default_metadata(rel_path: str):
    """Heuristic to determine metadata based on folder structure."""
    meta = {
        "type": "uncategorized",
        "priority": 1,
        "owner": "unknown",
        "version": "v1.0",
        "tags": []
    }
    
    path_parts = rel_path.split(os.sep)
    
    if "requirements" in path_parts:
        meta["type"] = "requirement"
        meta["priority"] = 5
    elif "references" in path_parts:
        meta["type"] = "reference"
        meta["priority"] = 2
    elif "policies" in path_parts:
        meta["type"] = "policy"
        meta["priority"] = 5
        
    return meta

def main():
    parser = argparse.ArgumentParser(description="Sync KB files to manifest.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_dir = os.path.join(base_dir, 'kb')
    manifest_path = os.path.join(base_dir, 'kb/manifest.yaml')

    # Load existing manifest
    if os.path.exists(manifest_path):
        try:
            manifest = load_yaml(manifest_path) or {}
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return
    else:
        manifest = {"documents": []}

    if "documents" not in manifest:
        manifest["documents"] = []

    # Index existing documents by path
    existing_docs = {doc['path']: doc for doc in manifest['documents']}
    
    # Scan physical files
    physical_files = get_all_files(kb_dir)
    
    added_count = 0
    updated_manifest_docs = []

    # Process all physical files
    for rel_path in physical_files:
        if rel_path in existing_docs:
            # Keep existing entry
            updated_manifest_docs.append(existing_docs[rel_path])
        else:
            # Create new entry
            added_count += 1
            new_doc = {
                "doc_id": generate_doc_id(rel_path),
                "path": rel_path,
                **determine_default_metadata(rel_path)
            }
            logger.info(f"[NEW] {rel_path} -> ID: {new_doc['doc_id']}, Type: {new_doc['type']}")
            updated_manifest_docs.append(new_doc)

    # Identify removed files (Optional: currently we just keep what's on disk)
    # To keep deleted files in manifest (for history), we would merge differently.
    # Here we sync to CURRENT disk state, so deleted files are removed from manifest.
    removed_count = len(manifest['documents']) - (len(updated_manifest_docs) - added_count)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} entries from manifest (files not found).")

    manifest['documents'] = updated_manifest_docs

    if args.dry_run:
        logger.info("Dry run complete. No changes written.")
    else:
        if added_count > 0 or removed_count > 0:
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest, f, sort_keys=False, allow_unicode=True)
            logger.info(f"Manifest updated: +{added_count} / -{removed_count}")
        else:
            logger.info("Manifest is up to date.")

if __name__ == "__main__":
    main()

