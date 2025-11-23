# LightRAG Service Template (v0.1)

> **로컬/사내 지식 기반 하이브리드(Graph + Vector) RAG 서비스 구축을 위한 템플릿**  
> LightRAG의 강력한 그래프 검색 기능을 CLI 및 API 형태로 쉽게 서빙할 수 있도록 설계된 스타터 킷입니다.

---

## 🌟 주요 특징

*   **Multi-Project Support**: 단일 인스턴스에서 여러 프로젝트(Knowledge Base)를 폴더 단위로 격리하여 운영할 수 있습니다.
*   **Dual Interface**: 관리자를 위한 **CLI 도구**와 서비스를 위한 **API 구조**(예정)를 모두 지원하는 아키텍처입니다.
*   **Hybrid Retrieval**: LightRAG의 `mix` 모드를 사용하여 그래프(관계)와 벡터(의미) 검색을 동시에 수행합니다.
*   **SoT (Single Source of Truth)**: `manifest.yaml`을 통해 문서의 정본, 버전, 우선순위를 체계적으로 관리합니다.

---

## 🚀 빠른 시작 (Quick Start)

이 프로젝트는 현재 **Mock 모드**가 기본 활성화되어 있어, 복잡한 설치나 API 키 없이 즉시 로직을 테스트해볼 수 있습니다.

### 1. 설치

```bash
# 1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install -r lightrag-local/requirements.txt
```

### 2. 문서 인덱싱 (Ingestion)

특정 프로젝트(`demo-project`)에 문서를 등록합니다.

```bash
# 기본 제공 샘플 문서를 'demo-project'라는 공간에 인덱싱
python lightrag-local/scripts/ingest.py --project demo-project
```

### 3. 질문하기 (Query)

등록한 프로젝트의 지식을 기반으로 질문합니다.

```bash
python lightrag-local/scripts/query.py "ProjectA의 핵심 요구사항은?" --project demo-project
```

---

## 🗓️ TODO: Service Roadmap

이 템플릿을 실제 상용 수준의 서비스로 발전시키기 위해 필요한 구현 사항들입니다. PR은 언제나 환영입니다!

- [ ] **API Server (`src/api.py`)**: FastAPI를 사용하여 REST API 엔드포인트(`POST /query`, `POST /ingest`) 구현
- [ ] **Async Ingestion**: 대용량 문서 처리 시 서버 블로킹 방지를 위한 비동기 큐(Celery/Redis) 연동
- [ ] **Dockerize**: `Dockerfile` 및 `docker-compose.yml` 추가로 원클릭 배포 환경 제공
- [ ] **Auth Integration**: 프로젝트별 접근 제어를 위한 간단한 API Key/Token 인증 미들웨어 추가

---

## 📚 운영 가이드: 지식 추가하기

문서를 추가하고 관리하는 방법은 매우 간단합니다.

### 방법 A: 자동 동기화 (추천)

1.  `lightrag-local/kb/` 아래 원하는 폴더(`requirements`, `references` 등)에 파일을 넣습니다.
2.  동기화 스크립트를 실행합니다.
    ```bash
    python lightrag-local/scripts/sync_manifest.py
    ```
    *   자동으로 `manifest.yaml`에 파일이 등록됩니다.
    *   `requirements/` 폴더의 파일은 중요도(Priority) **5**로 자동 설정됩니다.
3.  `ingest.py`를 실행하여 변경사항을 반영합니다.

### 방법 B: 수동 관리

1.  `lightrag-local/kb/manifest.yaml`을 열어 직접 항목을 추가합니다.
2.  `doc_id`, `path`, `priority` 등을 세밀하게 조정할 수 있습니다.

---

## ⚙️ 실전 모드 설정 (Real World Setup)

실제 **OpenAI API**와 **LightRAG 엔진**을 사용하려면 다음과 같이 설정하세요.

1.  **라이브러리 설치** (Git 설치 필요)
    ```bash
    pip install git+https://github.com/HKUDS/LightRAG.git
    # pip install git+https://github.com/HKUDS/RAG-Anything.git (선택)
    ```

2.  **API 키 설정**
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

3.  **Mock 모드 해제**
    `lightrag-local/src/rag_core.py` 파일을 열어 `_get_engine` 메서드 내의 주석을 해제하고 실제 `LightRAG` 인스턴스를 생성하도록 수정합니다.

---

## 📂 프로젝트 구조

```text
lightrag-local/
├── kb/                  # 지식 베이스 (문서 저장소)
│   ├── manifest.yaml    # 문서 메타데이터 관리 (SoT)
│   └── requirements/    # 예시 문서들
├── lightrag/            # LightRAG 엔진 데이터
│   ├── index/           # 프로젝트별 격리된 인덱스 저장소 ({project_name}/...)
│   └── config.yaml      # 엔진 설정
├── scripts/             # 실행 스크립트 (CLI Interface)
│   ├── ingest.py        # 파싱 및 인덱싱 실행 (--project 옵션 지원)
│   ├── query.py         # 질의 실행 (--project 옵션 지원)
│   └── sync_manifest.py # Manifest 자동 동기화 도구
└── src/                 # 핵심 로직 (Service Core)
    └── rag_core.py      # Multi-Project 지원 RAG 엔진 매니저
```

