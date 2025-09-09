from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import uvicorn
from typing import Optional, List, Dict
from rag_system import get_rag_system
from config import settings

# 서버 생성
app = FastAPI(title="복약지도 챗봇 API", version="1.0.0", description="RAG 기반 복약지도 챗봇 서비스")

# CORS 설정 (프론트엔드와 연결을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델 
class ChatRequest(BaseModel):
    message: str  

class SourceInfo(BaseModel):
    rank: int
    source: str
    category: str
    similarity: float
    url: str = ""

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceInfo] = []
    search_results: List[Dict] = []
    model_used: str = "rag-gpt4"
    processing_time: Optional[float] = None

def check_emergency_keywords(query: str) -> List[str]:
    """기본 안전성 경고 체크"""
    warnings = []
    
    emergency_keywords = ["응급", "급성", "중독", "쇼크", "호흡곤란", "의식잃음"]
    pregnancy_keywords = ["임신", "임산부", "수유", "모유"]

    for keyword in emergency_keywords:
        if keyword in query:
            warnings.append("🚨 응급상황이 의심됩니다. 즉시 119에 연락하거나 응급실로 가세요!")
            break
    
    for keyword in pregnancy_keywords:
        if keyword in query:
            warnings.append("⚠️ 임신/수유 중에는 반드시 의사와 상담 후 복용하세요.")
            break

    return warnings


@app.get("/")
async def root():
    return {"message" : "복약지도 Copilot API 서버가 정상 작동 중 입니다. 🤖"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG 기반 채팅 엔드포인트"""

    start_time = time.time()

    # 사용자가 보낸 메세지
    user_message = request.message

    # 1. 응급상황 우선 체크
    emergency_warnings = check_emergency_keywords(user_message)
    if emergency_warnings:
        return ChatResponse(
            response=emergency_warnings[0] + "\n\n전문 의료진의 진료가 필요합니다.",
            sources=[],
            search_results=[],
            model_used="emergency_rule",
            processing_time=time.time() - start_time
        )
    
    try:
        # 2. RAG 시스템 처리
        rag_system = get_rag_system()
        result = rag_system.process_query(user_message)

        # 3. 응답 구성
        sources = [
            SourceInfo(
                rank=src["rank"],
                source=src["source"],
                category=src["category"],
                similarity=src["similarity"],
                url=src.get("url", "")
            ) for src in result.get("sources", [])
        ]

        processing_time = time.time() - start_time

        return ChatResponse(
            response=result["response"],
            sources=sources,
            search_results=result.get("search_results", []),
            model_used=result.get("model_used", "rag-gpt4"),
            processing_time=processing_time
        )

    except Exception as e:
        print(f"RAG 시스템 오류: {e}")
        return ChatResponse(
            response="죄송합니다. 서버 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            sources=[],
            search_results=[],
            model_used="error",
            processing_time=time.time() - start_time
        )

@app.get("/api/drugs")
async def get_all_drugs():
    """현재 시스템에 등록된 약물 목록 조회"""
    try:
        rag_system = get_rag_system()
        
        # 벡터 db에 저장된 약물들 추출
        if not rag_system.documents:
            return {"drugs": [], "message": "등록된 약물이 없습니다."}
        
        # 중복 제거된 약물명 목록 생성
        unique_drugs = set()
        for doc in rag_system.documents:
            drug_name = doc.get("drug_name") or doc.get("product_name")
            if drug_name:
                unique_drugs.add(drug_name)
        
        drug_list = sorted(list(unique_drugs))
        
        return {
            "drugs": drug_list,
            "total_count": len(drug_list),
            "total_documents": len(rag_system.documents)
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
