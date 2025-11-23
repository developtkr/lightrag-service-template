import os
import yaml
import logging
import hashlib
from typing import Dict, Any, Optional, List

from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
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
        
        # Resolve working_dir relative to the project root (lightrag-local), not CWD
        # Assuming this file is in src/rag_core.py, parent of parent is project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Get config path or default
        rel_work_dir = config.get('working_dir', './lightrag/index')
        if rel_work_dir.startswith('./'):
            rel_work_dir = rel_work_dir[2:]
            
        self.base_working_dir = os.path.join(project_root, rel_work_dir)
        
        # Cache for loaded engines: {project_name: engine_instance}
        self.engines: Dict[str, LightRAG] = {}
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        if not os.path.exists(self.base_working_dir):
            os.makedirs(self.base_working_dir)

    def _get_engine(self, project_name: str = "default") -> LightRAG:
        """
        Lazy loads or creates a LightRAG engine instance for a specific project.
        """
        if project_name in self.engines:
            return self.engines[project_name]

        # Project-specific directory: .../lightrag/index/{project_name}
        project_working_dir = os.path.join(self.base_working_dir, project_name)
        
        if not os.path.exists(project_working_dir):
            os.makedirs(project_working_dir)
            logger.info(f"Created new index directory for project: {project_name}")

        logger.info(f"Initializing RAG Engine for project '{project_name}' at {project_working_dir}...")
        
        # Initialize Real LightRAG
        # Note: We use the helper functions mapped from config string if needed,
        # but here we hardcode standard OpenAI ones for simplicity as per 'best' request for now.
        # In a full generic implementation, we would map config strings to functions.
        
        # Using standard OpenAI binding from LightRAG defaults or explicit functions
        # LightRAG's default llm_model_func is often gpt-4o-mini or similar depending on version.
        # We explicitly set them to match the config intent.
        
        engine = LightRAG(
            working_dir=project_working_dir,
            llm_model_func=gpt_4o_mini_complete,  # Using mini for indexing as per config default intention often
            # Note: LightRAG typically allows separate funcs for different tasks, 
            # but constructor usually takes one main llm_model_func. 
            # Use kwargs if specific separation is needed (e.g. llm_model_max_async)
            # For simplicity and 'best' start, we use the efficient one.
        )
        
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
        
        # LightRAG insert
        engine.insert(text)

    def query(self, text: str, mode: str = "mix", project_name: str = "default") -> str:
        """
        Unified interface for query.
        """
        engine = self._get_engine(project_name)
        logger.info(f"Querying project '{project_name}': '{text}' (mode={mode})")
        
        param = QueryParam(mode=mode)
        return engine.query(text, param=param)

def parse_document(file_path: str) -> str:
    """
    Simple text parser.
    """
    logger.info(f"Parsing {file_path}...")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return ""
