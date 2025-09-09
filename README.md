# 🏥 Medi-Mate: 환자 복약지도 AI 챗봇

> **안전하고 근거 기반의 의료 정보를 제공하는 RAG 기반 복약지도 챗봇**

<div align="center">

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

[🚀 Live Demo](#) • [📖 Documentation](#사용법) • [🐛 Issues](https://github.com/yujeong0411/medi-mate/issues)

</div>

## 📋 프로젝트 개요

**Medi-Mate**는 환자가 안전하고 정확한 복약 정보를 쉽게 얻을 수 있도록 돕는 RAG 기반 챗봇입니다. 의료진 상담을 **대체하지 않고 보완**하는 역할을 하며, 모든 응답에 **근거와 출처**를 명시하여 신뢰성을 보장합니다.

### ✨ 주요 특징

- 🔍 **RAG 기반 검색**: 관련 의료 문서를 검색하여 근거 기반 응답 제공
- 🛡️ **안전성 우선**: 응급상황 감지, 의료진 상담 권유, 환각 방지
- 📱 **모바일 최적화**: 메신저 스타일의 직관적인 채팅 인터페이스
- 🔗 **출처 투명성**: 모든 답변에 검색된 문서 출처 및 유사도 점수 제공
- ⚡ **실시간 응답**: 타이핑 효과와 로딩 애니메이션으로 자연스러운 UX

### 🎯 지원 기능

- 약물 복용법 안내 (용량, 횟수, 시간)
- 금기사항 및 주의사항 제공
- 약물 상호작용 정보
- 부작용 관리 가이드
- 응급상황 인식 및 안내

## 🏗️ 시스템 아키텍처

```
User → React Frontend → FastAPI Backend → RAG System
                                         ├── Embedding Model (한국어 특화)
                                         ├── Vector DB (FAISS)
                                         ├── Document Store
                                         └── OpenAI API (응답 생성)
```

### 🔄 RAG 파이프라인

1. **문서 인덱싱**: 의료 문서들을 벡터로 변환하여 FAISS에 저장
2. **쿼리 처리**: 사용자 질문을 벡터로 변환
3. **유사도 검색**: 벡터 공간에서 가장 관련성 높은 문서 검색
4. **응답 생성**: 검색된 문서를 컨텍스트로 OpenAI에서 답변 생성
5. **안전성 검증**: 의료 안전 규칙 적용 및 출처 명시

## 🛠️ 기술 스택

### Frontend
- **React 18** + **Vite**: 빠른 개발 환경
- **Tailwind CSS**: 모바일 우선 반응형 디자인
- **Axios**: API 통신
- **Lucide React**: 아이콘

### Backend
- **FastAPI**: 비동기 웹 프레임워크
- **Python 3.12.4**:비동기 처리
- **CORS**: 크로스 오리진 처리

### AI/ML
- **OpenAI GPT-4o-mini**: 응답 생성
- **한국어 특화 Transformer**: 임베딩 모델
- **FAISS**: 벡터 인덱스
- **직접 구현 RAG 시스템**: 의료 도메인 특화

## 📁 프로젝트 구조

```
Medi-Mate/
├── frontend/                    # React 앱
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatInterface.jsx    # 모바일 최적화 채팅 UI
│   │   ├── services/
│   │   │   └── api.js              # Axios 기반 API 클라이언트
│   │   ├── App.jsx
│   │   ├── index.css               # Tailwind 설정
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/                     # FastAPI 서버
│   ├── main.py                 # FastAPI 메인 서버
│   ├── rag_system.py          # RAG 시스템 (핵심)
│   ├── common_parser.py  
│   ├── data_builder.py  
│   ├── kfda_data_handler.py  
│   ├── direct_embedder.py  
│   ├── .env                   # API 키 환경변수
│   └── requirements.txt
│
└── README.md
```

## 🚀 설치 및 실행

### 사전 요구사항

- Node.js 22.11.0
- Python 3.12.4
- OpenAI API 키
- 공공 데이터 포털(식품의약품안전처_의약품개요정보(e약은요)) API 키

### 1. 저장소 클론

```bash
git clone https://github.com/yujeong0411/medi-mate.git
cd medi-mate
```

### 2. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/Scripts/activate 

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 추가

# 서버 실행
uvicorn main:app --reload
# 서버: http://localhost:8000
```

### 3. 프론트엔드 설정

```bash
cd ../medi-mate

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
# 클라이언트: http://localhost:5173
```

### 4. RAG 시스템 테스트

```bash
# RAG 시스템 테스트
python -c "from rag_system import get_rag_system; rag = get_rag_system(); print('성공')"

# API 테스트
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "타이레놀 복용법 알려줘"}'
```

## 💊 사용법

### 기본 질문 예시

- "타이레놀 몇 시간마다 먹어야 하나요?"
- "임신 중에 먹으면 안 되는 약이 있나요?"
- "애드빌과 타이레놀 같이 먹어도 되나요?"
- "복용 중인 약의 부작용이 있다면?"

### 안전 기능

- **응급상황 감지**: 심각한 증상 언급 시 즉시 응급실 방문 권유
- **의료진 상담 권유**: 복잡한 사례나 개인 맞춤 상담 필요 시 전문의 상담 권유
- **디스클레이머**: 모든 응답에 의료진 상담의 중요성 명시

## 🔧 주요 기능

### 🔍 하이브리드 검색
- 약물명 + 증상 통합 검색으로 검색 커버리지 극대화
- 실시간 RAG로 사용자 질문에 맞춘 관련 문서 검색

### 🛡️ 안전장치
- 응급상황 자동 감지
- 임신/수유부 특별 경고
- 환각 방지 프롬프트 적용

### 📱 사용자 경험
- 메신저 스타일 UI (카카오톡 유사)
- 실시간 타이핑 효과
- 빠른 응답 버튼 (자주 묻는 질문 2x2 그리드)
- 출처 클릭으로 근거 확인 가능

## 📊 성능 및 평가

### 측정 지표
- **정확도**: 의료 정보의 정확성
- **출처 제시율**: 응답에 근거 명시 비율
- **환각률 감소**: 잘못된 정보 생성 최소화
- **응답 지연시간**: 사용자 경험 최적화

### 품질 보장
- 의료 전문 프롬프트 엔지니어링
- 다단계 안전성 검증
- 출처 투명성 보장

## 🚀 향후 발전 방향

### 단기 개선 (1-2개월)
- [ ] 약물 데이터베이스 확장 (50+ 약물)
- [ ] 고급 안전성 규칙 추가
- [ ] 사용자 피드백 시스템
- [ ] 성능 모니터링 대시보드

### 중기 발전 (3-6개월)
- [ ] BGE-M3 임베딩 모델 업그레이드
- [ ] 의료 문서 자동 수집 파이프라인
- [ ] 다중 언어 지원
- [ ] 음성 인터페이스 추가

### 장기 비전 (6개월+)
- [ ] 의료 전문가 검증 시스템
- [ ] 개인화 복약 관리
- [ ] 의료기관 API 연동
- [ ] 모바일 앱 개발

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 의료 면책조항

**Medi-Mate는 의료진의 진단이나 처방을 대체할 수 없습니다.** 모든 의료 결정은 반드시 의료 전문가와 상담하시기 바랍니다. 응급상황 시에는 즉시 응급실을 방문하거나 119에 신고하세요.

## 📞 문의

- **이메일**: [choiyujeong0411@gmail.com]
- **프로젝트 링크**: [https://github.com/yujeong0411/medi-mate](https://github.com/yujeong0411/medi-mate)

---

<div align="center">

**🏥 안전한 의료 정보, Medi-Mate와 함께 🤖**

[⭐ Star this repo](https://github.com/yujeong0411/medi-mate) • [🐛 Report Bug](https://github.com/yujeong0411/medi-mate/issues) • [💡 Request Feature](https://github.com/yujeong0411/medi-mate/issues)

</div>