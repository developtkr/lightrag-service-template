import os
import yaml
import logging
import hashlib
from typing import Dict, Any, Optional, List

# Placeholder imports for future Real Implementation
# from lightrag import LightRAG, QueryParam

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        # Return empty dict instead of raising error to allow for graceful degradation/init
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: str, data: Dict[str, Any]):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    if not os.path.exists(file_path):
        return ""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {file_path}: {e}")
        return ""

class RAGService:
    """
    Encapsulates LightRAG interactions.
    Supports Multi-tenancy by managing separate LightRAG instances per project_name.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_working_dir = config.get('working_dir', './lightrag/index')
        # Cache for loaded engines: {project_name: engine_instance}
        self.engines: Dict[str, Any] = {}
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        if not os.path.exists(self.base_working_dir):
            os.makedirs(self.base_working_dir)

    def _get_engine(self, project_name: str = "default"):
        """
        Lazy loads or creates a LightRAG engine instance for a specific project.
        """
        if project_name in self.engines:
            return self.engines[project_name]

        # Project-specific directory: ./lightrag/index/{project_name}
        project_working_dir = os.path.join(self.base_working_dir, project_name)
        
        if not os.path.exists(project_working_dir):
            os.makedirs(project_working_dir)
            logger.info(f"Created new index directory for project: {project_name}")

        logger.info(f"Initializing RAG Engine for project '{project_name}' at {project_working_dir}...")
        
        # In v0, this is a mock. In real impl, instantiate LightRAG here.
        # engine = LightRAG(working_dir=project_working_dir, ...)
        engine = f"MockLightRAGInstance(project={project_name})"
        
        # Cache the instance
        self.engines[project_name] = engine
        return engine

    def ingest_text(self, text: str, metadata: Optional[Dict] = None, project_name: str = "default"):
        """
        Unified interface for ingestion.
        """
        if not text:
            logger.warning("Skipping empty text ingestion.")
            return
        
        engine = self._get_engine(project_name)
        logger.info(f"Ingesting text for project '{project_name}' (len={len(text)})...")
        # engine.insert(text)

    def query(self, text: str, mode: str = "mix", project_name: str = "default") -> str:
        """
        Unified interface for query.
        """
        engine = self._get_engine(project_name)
        logger.info(f"Querying project '{project_name}': '{text}' (mode={mode})")
        # param = QueryParam(mode=mode)
        # return engine.query(text, param=param)
        return f"Mock Answer for '{text}' from project '{project_name}' context.\n(Mode: {mode})"

def parse_document(file_path: str) -> str:
    """
    Wrapper for RAG-Anything parsing.
    """
    logger.info(f"Parsing {file_path}...")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ""
    
    # Mock Parsing Logic
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return ""
