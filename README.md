# ATL_Converter

> **Advantest T5833 Memory Tester Pattern & Prescramble 자동 변환/수정 도구**

본 프로젝트는 Advantest의 대표 메모리 테스터인 **T5833**의 **ALPG Pattern** 및 **Prescramble** 소스 코드를 파싱하고, 핀 배치 변경, 타이밍 세트(TS) 재매핑, 어드레스/데이터 스크램블 수식 변환 등을 안전하고 신속하게 수행하기 위한 변환기(Converter)입니다.

3명의 엔지니어가 각자의 **AI 코딩 에이전트**와 협업하여 개발할 수 있도록 설계되었으며, 사내 Git 기반 CI/CD 파이프라인 및 AI 도메인 가이드가 포함되어 있습니다.

---

## 📚 주요 문서 바로가기

- 📖 [**개발 및 CI/CD 전략서 (DEVELOPMENT_STRATEGY.md)**](file:///c:/python/ATL_Converter/docs/DEVELOPMENT_STRATEGY.md)  
  - 3인 팀 역할 분담 및 인터페이스 분리 전략
  - AI 페어 프로그래밍 시 커밋/PR 규칙 (Trunk-based)
  - 사내 Git 서버 CI/CD 파이프라인 (GitLab CI, GitHub Actions) 구성
- 🤖 [**T5833 AI Agent 도메인 가이드 (T5833_AGENT_GUIDE.md)**](file:///c:/python/ATL_Converter/docs/T5833_AGENT_GUIDE.md)  
  - 사내 AI 에이전트에게 주입할 T5833 Pattern(1/2/4-way), SDEF 및 Prescramble 문법/구조
  - 핵심 기능 정의 (FR-1 ~ FR-9) 및 **Few-Shot 예제 5종**
  - AI 에이전트 황금 규칙 (Golden Rules)
- 🔒 [**사내 Agent 튜닝 & 보안 가이드 (IN_HOUSE_AGENT_TUNING_GUIDE.md)**](file:///c:/python/ATL_Converter/docs/IN_HOUSE_AGENT_TUNING_GUIDE.md)  
  - 외부 노출 불가 실제 사내 파일로 사내 Agent에게 가이드를 자율 업데이트시키는 프롬프트 템플릿
  - 실제 패턴 비식별화 도구 (`scripts/sanitize_sample.py`) 사용법


---

## 🛠 빠른 시작 가이드 (uv 기반)

사내 표준 가상환경 도구인 `uv`를 사용하여 환경을 설정합니다.

### 1. 가상환경 생성 및 패키지 설치
```bash
# 가상환경 .venv 생성
uv venv .venv

# 가상환경 활성화 (Windows PowerShell)
.venv\Scripts\activate

# 의존성 및 개발 도구 설치
uv pip install -e ".[dev]"
```

### 2. 코드 린트 및 포맷팅 검사
```bash
ruff check .
ruff format --check .
mypy src/
```

### 3. 단위 테스트 및 Golden Sample 회귀 테스트 실행
```bash
pytest -v
```

---

## 💻 CLI 기본 사용법

```bash
# 1. 특정 명령어(INCX)에 대한 타이밍 세트(TS1 -> TS3) 일괄 치환
python -m atl_converter.cli modify-ts tests/fixtures/sample_pattern.pat output_pat.pat -f TS1 -t TS3 -i INCX

# 2. Prescramble 수식 기반 논리 -> 물리 주소 변환 시뮬레이션
python -m atl_converter.cli test-scramble tests/fixtures/sample_scramble.scram --x 3 --y 1
```

---

## 📁 디렉토리 구조

```text
ATL_Converter/
├── .github/workflows/ci.yml    # 사내 GitHub / Gitea용 CI 워크플로우
├── .gitlab-ci.yml             # 사내 GitLab CI 파이프라인 설정
├── docs/
│   ├── DEVELOPMENT_STRATEGY.md # 3인 협업 + CI/CD 개발 전략
│   └── T5833_AGENT_GUIDE.md    # AI 에이전트 주입용 T5833 지식 & Few-shot
├── src/
│   └── atl_converter/
│       ├── __init__.py
│       ├── models.py          # Pattern 및 Scramble IR 데이터 모델
│       ├── pattern_parser.py  # ALPG Pattern 파서 및 수정 모듈
│       ├── scramble_engine.py # Prescramble 수식 파서 및 계산 엔진
│       └── cli.py             # CLI 엔드포인트
├── tests/
│   ├── fixtures/              # T5833 골든 샘플 파일 (.pat, .scram)
│   ├── test_pattern.py        # 패턴 파서/변환 단위 테스트
│   └── test_scramble.py       # 스크램블 계산 단위 테스트
├── pyproject.toml             # uv / 패키징 / 도구 설정
└── README.md
```
