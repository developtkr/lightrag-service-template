import os
import sys
import argparse

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_core import RAGService, load_yaml

def main():
    parser = argparse.ArgumentParser(description="Query the LightRAG Agent")
    parser.add_argument("query", type=str, help="The question to ask")
    parser.add_argument("--mode", type=str, default="mix", choices=["local", "global", "hybrid", "naive", "mix"], help="Retrieval mode")
    parser.add_argument("--project", type=str, default="default", help="Project name for knowledge base isolation")
    args = parser.parse_args()

    # 1. Configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = load_yaml(os.path.join(base_dir, 'lightrag/config.yaml'))

    # 2. Initialize Service
    rag = RAGService(config)

    # 3. Execute Query
    result = rag.query(args.query, mode=args.mode, project_name=args.project)

    print("\n=== Answer ===")
    print(result)

if __name__ == "__main__":
    main()
