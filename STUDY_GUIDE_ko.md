# FireTwin-Lite 3주 학습·구현 가이드

목표: 3주 뒤 GitHub에 올라간 프로젝트를 면접에서 **직접 설명하고 시연**할 수 있는 상태.
원칙: 코드를 복사해서 돌리는 게 아니라, 각 파일이 **왜 그렇게 생겼는지** 말로 설명할 수 있을 때 다음 단계로 넘어간다.

---

## 0일차: 환경 준비 (1~2시간)

1. 설치: **Git**, **Python 3.11 이상**, **VS Code**
2. VS Code 확장: **Python**(Microsoft), **Stardog RDF Grammars** 또는 **Turtle Language Server**(.ttl 색칠), **SPARQL** 하이라이터
3. GitHub에 `firetwin-lite` 저장소 만들기 (Public, README 없이 빈 저장소)
4. 받은 압축 파일을 풀고, VS Code에서 `firetwin-lite` 폴더 열기
5. VS Code 터미널(Ctrl+`)에서:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m pip install -e .
python -m firetwin.stage1       # 결과가 출력되면 성공
pytest                          # 3 passed
```

6. GitHub에 첫 업로드:

```bash
git init
git add .
git commit -m "Stage 1: fire-safety knowledge graph with SPARQL and SHACL"
git branch -M main
git remote add origin https://github.com/syHong23/firetwin-lite.git
git push -u origin main
```

---

## 1주차: 1단계를 완전히 내 것으로 (지식 그래프)

### 파일별로 이해할 것

| 파일 | 이해해야 할 개념 | 스스로 답해볼 질문 |
|---|---|---|
| `ontology/firetwin.ttl` | 클래스, 하위 클래스, 속성, 정의역·치역 | 왜 SmokeDetector를 sosa:Sensor의 하위 클래스로 두었나? |
| `ontology/building.ttl` | 인스턴스, BOT의 hasStorey·hasSpace·containsElement | 방과 감지기는 어떤 속성으로 연결되나? |
| `queries/*.rq` | SELECT, FILTER NOT EXISTS, GROUP BY, COUNT | "감지기 없는 방" 질의는 어떻게 동작하나? |
| `src/firetwin/kg.py` | OWL 2 RL 추론(owlrl), SHACL 검증(pyshacl) | 추론 전 131개, 후 473개 트리플: 무엇이 늘었나? |
| `shapes/fire_rules.ttl` | SHACL NodeShape, qualifiedMinCount, 경로(path) | SPARQL 질의와 SHACL 규칙은 무엇이 다른가? |

### 핵심 개념 3가지 (면접 단골)

- **온톨로지 vs 지식 그래프**: 온톨로지는 개념과 관계의 "설계도"(firetwin.ttl), 지식 그래프는 그 설계도로 채운 "실제 데이터"(building.ttl).
- **추론(reasoning)**: 명시하지 않은 사실을 규칙으로 끌어냄. 데이터에는 "SD_001은 SmokeDetector"만 있지만, 추론으로 "SD_001은 sosa:Sensor"가 됨.
- **SPARQL vs SHACL**: SPARQL은 "질문하기", SHACL은 "규칙을 지키는지 검사하기". LLM 답의 검증에는 둘 다 쓴다.

### 직접 해볼 연습 (꼭 하기)

1. `building.ttl`에서 Room103에 연기 감지기를 추가 → SHACL이 "conforms"가 되는지 확인
2. 3층(S2)과 방 2개를 추가하고, 일부러 수동 발신기를 빼서 규칙 2가 잡는지 확인
3. 새 질의 작성: "화재 구획 B에 있는 모든 감지기"
4. 새 SHACL 규칙 작성: "모든 층에는 비상구가 있는 공간이 최소 하나 있어야 한다" (힌트: 비상구는 exitFrom으로 공간과 연결됨)
5. Protégé로 `firetwin.ttl`을 열어 클래스 계층을 그림으로 보기

연습마다 커밋하기: `git commit -m "Add storey S2 and call-point rule"`

---

## 2주차: 2단계 (근거 기반 LLM과 검증) — 프로젝트의 핵심

1. **Ollama 설치** → 터미널에서 `ollama pull llama3.1:8b` 또는 `ollama pull mistral` (4비트 양자화 모델이 기본)
2. **기본 호출**: 파이썬에서 Ollama에 질문 보내기 (LangChain의 `ChatOllama` 사용 가능, 이미 써본 방식과 같음)
3. **RAG 만들기**: 질문 → 관련 SPARQL 실행 → 결과 트리플을 프롬프트에 넣기 → 답변
4. **검증 계층**: LLM이 JSON으로 답하고 근거 엔티티 ID를 포함 → ID가 그래프에 있는지 SPARQL로 확인 → 틀리면 이유를 붙여 다시 묻기
5. **실험**: 질문 30개를 만들고 세 조건 비교 (LLM만 / RAG / RAG+검증) → 정확도, 존재하지 않는 방·감지기를 말한 비율(환각률), 응답 시간 표로 정리

이 실험 결과표가 면접의 가장 강한 무기예요. Elith에서의 교훈("스키마는 형식만 보장한다")을 숫자로 증명하는 거니까요.

---

## 3주차: 3단계 (에이전트와 플랫폼)

1. **LangGraph**: Elith 교육 실습의 다중 에이전트 구조를 그대로 응용
   - 대피 에이전트: 화재 구획을 피하는 경로 탐색 도구(networkx)
   - 점검 에이전트: 감지기 시계열에서 이상 탐지
   - 오케스트레이터: 우선순위(사람의 안전 > 접근성 > 자원 절약), 중요한 결정 전 사람의 승인(interrupt)
2. **MQTT**: Mosquitto + paho-mqtt로 가상 감지기 데이터 흘려보내기, 일부 감지기에 드리프트 넣기
3. **FastAPI**: `/ask`, `/evacuate` 같은 엔드포인트
4. **Docker Compose**: Ollama, API, MQTT를 한 번에 실행
5. **GitHub Actions**: push할 때마다 pytest 자동 실행

시간이 부족하면 3단계는 에이전트 + FastAPI까지만 해도 충분해요. 2단계 실험이 더 중요합니다.

---

## 매일의 리듬

- 하루 시작: 어제 커밋 메시지 읽기 → 오늘 할 일 한 줄 적기
- 하루 끝: 작게라도 커밋 + README 체크박스 갱신
- 막히면: 에러 메시지 전체를 복사해서 질문하기

## 지원서 보내기 전 체크

- [ ] 저장소가 Public이고 README에 실행 방법과 결과가 있다
- [ ] 커버레터에 쓴 내용(Ollama, SPARQL·SHACL 검증, Docker, MQTT)이 저장소에 실제로 있다
- [ ] 그 부분을 화면 공유로 5분 안에 시연할 수 있다
- [ ] 마감(11월 15일)보다 충분히 앞서 보낸다
