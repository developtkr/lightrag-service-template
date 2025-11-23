# Context Contract (v0)

RETRIEVED_SNIPPETS는 배열 형태로 입력된다.

[
  {
    "doc_id": "...",
    "title": "...",
    "version": "...",
    "type": "...",
    "priority": 1-5,
    "score": 0.0-1.0,
    "text": "..."
  }
]

규칙:
1) 답변은 RETRIEVED_SNIPPETS에 근거한 내용만 포함한다.
2) 근거 부족이면 "근거 부족/확인 필요"를 명시한다.
3) 사용한 doc_id를 답변 끝에 짧게 나열한다.

