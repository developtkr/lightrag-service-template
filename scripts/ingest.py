import os
import sys
import logging
import hashlib

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_core import RAGService, load_yaml, save_yaml, setup_logging, parse_document, calculate_file_hash

setup_logging()
logger = logging.getLogger(__name__)

DEFAULT_METADATA = {
    "type": "uncategorized",
    "priority": 1,
    "owner": "unknown",
    "version": "auto-v1"
}

def generate_doc_id(file_path: str) -> str:
    """Generate a consistent doc_id based on file path hash."""
    base_name = os.path.basename(file_path)
    name_part = os.path.splitext(base_name)[0]
    return name_part

def get_all_files(kb_dir: str):
    """Recursively get all supported files in kb directory."""
    supported_exts = {'.md', '.txt', '.pdf', '.docx', '.pptx'}
    all_files = []
    for root, _, files in os.walk(kb_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                # Store relative path from kb directory
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, kb_dir)
                all_files.append(rel_path)
    return all_files

def main():
    # 0. Parse Args
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into LightRAG")
    parser.add_argument("--project", type=str, default="default", help="Target project name for ingestion")
    args = parser.parse_args()

    # 1. Configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_dir = os.path.join(base_dir, 'kb')
    config = load_yaml(os.path.join(base_dir, 'lightrag/config.yaml'))
    manifest_path = os.path.join(base_dir, 'kb/manifest.yaml')
    
    manifest = load_yaml(manifest_path)
    if "documents" not in manifest:
        manifest["documents"] = []
    
    # Create a lookup map for existing manifest entries (mutable for updates)
    manifest_map = {doc['path']: doc for doc in manifest['documents']}
    original_manifest_len = len(manifest['documents'])

    # 2. Initialize Service
    rag = RAGService(config)
    
    # 3. Scan & Ingest Loop
    physical_files = get_all_files(kb_dir)
    logger.info(f"Scanning KB directory: found {len(physical_files)} files.")
    
    processed_count = 0
    skipped_count = 0
    failed_files = []
    manifest_updated = False

    for rel_path in physical_files:
        file_path = os.path.join(kb_dir, rel_path)
        current_hash = calculate_file_hash(file_path)
        
        # Determine Metadata & Check Hash
        doc_info = None
        is_new_or_changed = False

        if rel_path in manifest_map:
            # Case A: Listed in Manifest
            doc_info = manifest_map[rel_path]
            last_hash = doc_info.get('last_hash', '')
            
            if current_hash != last_hash:
                is_new_or_changed = True
                logger.info(f"Processing [Update]: {rel_path}")
            else:
                skipped_count += 1
                # logger.debug(f"Skipping [No Change]: {rel_path}")
                continue
        else:
            # Case B: Unlisted (Implicit/Default)
            if rel_path == "manifest.yaml": 
                continue
                
            is_new_or_changed = True
            doc_info = DEFAULT_METADATA.copy()
            doc_info['path'] = rel_path
            doc_info['doc_id'] = generate_doc_id(file_path)
            
            if "requirements" in rel_path:
                doc_info['type'] = "requirement"
                doc_info['priority'] = 3
            elif "references" in rel_path:
                doc_info['type'] = "reference"
            
            # Add to map (in-memory manifest update)
            manifest_map[rel_path] = doc_info
            # Note: We don't automatically save unlisted files to manifest.yaml here 
            # to keep ingestion purely about index state. 
            # Use sync_manifest.py for structural updates.
            # BUT, we need to track hash if we want to skip it next time.
            # So for "virtual" entries, hash tracking is in-memory only unless we sync.
            logger.info(f"Processing [New/Default]: {rel_path}")

        # Parse
        content = parse_document(file_path)
        
        if not content:
            logger.warning(f"Skipping empty content or parse error: {rel_path}")
            failed_files.append({"path": rel_path, "reason": "Empty content or parse error"})
            continue

        # Ingest
        try:
            rag.ingest_text(content, metadata=doc_info, project_name=args.project)
            
            # Update Hash in Manifest (Only if it's a tracked file)
            if rel_path in manifest_map:
                manifest_map[rel_path]['last_hash'] = current_hash
                manifest_updated = True
            
            processed_count += 1
        except Exception as e:
            logger.error(f"Ingestion failed for {rel_path}: {e}")
            failed_files.append({"path": rel_path, "reason": str(e)})

    # 4. Save Manifest Update (if hashes changed)
    if manifest_updated:
        # Reconstruct list from map to preserve updates
        # Note: This only updates entries that were already in the manifest or added to map
        # Be careful not to lose order or structure. 
        # Safest is to update the original list objects in place.
        for i, doc in enumerate(manifest['documents']):
            path = doc['path']
            if path in manifest_map:
                manifest['documents'][i] = manifest_map[path]
        
        save_yaml(manifest_path, manifest)
        logger.info("Updated manifest.yaml with new file hashes.")

    # 5. Final Report
    logger.info("="*40)
    logger.info("Ingestion Summary")
    logger.info(f"Total Files Scanned: {len(physical_files)}")
    logger.info(f"Processed (New/Changed): {processed_count}")
    logger.info(f"Skipped (Unchanged): {skipped_count}")
    logger.info(f"Failed: {len(failed_files)}")
    
    if failed_files:
        logger.info("-" * 20)
        logger.info("Failure Details:")
        for fail in failed_files:
            logger.info(f" - {fail['path']}: {fail['reason']}")
    logger.info("="*40)

if __name__ == "__main__":
    main()
