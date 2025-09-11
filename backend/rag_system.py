import os
import json
import faiss
import numpy as np
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from kfda_data_handler import get_data_handler, search_medical_data
from embedder import UpstageEmbedder
from common_parser import create_embedding_content

# Responses API가 새로 나왔지만, 안정성을 위해 Chat Completions API 사용

load_dotenv()

class MedicalRAGSystem:
    """영구 저장 가능한 FAISS 기반 RAG 시스템"""

    def __init__(self, data_dir="./data"):
        # 경로 설정
        self.data_dir = data_dir
        self.index_path = os.path.join(data_dir, "medical_docs.index")
        self.documents_path = os.path.join(data_dir, "documents.json")

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

        # OPENAI 설정
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 임베딩 모델
        self.embedder = UpstageEmbedder(model_name="solar-embedding-1-large-passage")

        # 식약처 데이터 T
        self.data_handler = get_data_handler()

        # FAISS 인덱스와 메타데이터
        self.index = None
        self.documents = []

        # 시스템 초기화
        self._initialize_system()

    def _initialize_system(self):
        """시스템 초기화: 기존 인덱스 로드 또는 새로 생성"""
        if self._load_existing_index():
            print("기존 FAISS 인덱스 로드 완료")
        else:
            print("벡터 DB가 없습니다. 별도 구축 도구를 사용하세요.")
            # 빈 인덱스로 시작
            self.index = None
            self.documents = []

    def _load_existing_index(self) -> bool:
        """기존 인덱스 로드"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.documents_path):
                # FAISS 인덱스 로드
                self.index = faiss.read_index(self.index_path)
                
                # 메타데이터 로드
                with open(self.documents_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data['documents']
                
                return True
                
        except Exception as e:
            print(f"기존 인덱스 로드 실패: {e}")

        return False

    def _rebuild_index(self, documents: List[Dict]):
        """인덱스 재구축"""
        
        # 임베딩 생성
        contents = [doc["content"] for doc in documents]
        embeddings = self.embedder.encode(contents)
        
        # FAISS 인덱스 생성
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # L2 정규화 후 추가
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        
        self.documents = documents
        
        # 디스크에 저장
        self._save_to_disk()

    def _save_to_disk(self):
        """인덱스를 디스크에 저장"""
        try:
            # FAISS 인덱스 저장
            faiss.write_index(self.index, self.index_path)
            
            data = {
                'documents': self.documents,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.documents_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 마지막 업데이트 시간 저장
            with open(self.last_update_path, 'w') as f:
                f.write(datetime.now().isoformat())
            
        except Exception as e:
            print(f"디스크 저장 실패: {e}")
            
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """쿼리와 유사한 문서 검색 - 벡터 검색"""
        if self.index is None:
            return []
        
        # 1. 쿼리를 벡터로 변환
        query_embedding = self.embedder.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # 2. FAISS에서 코사인 유사도 계산 + 검색
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # 3. 유사도 점수와 함께 결과 반환
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1 and idx < len(self.documents):  # 유효한 인덱스
                doc = self.documents[idx]
                results.append({
                    **doc,  # 직접 필드 방식 - 전체 문서 그대로
                    "similarity_score": float(score),
                })
        
        return results

    def search_with_api(self, query: str) -> List[Dict]:
        """실시간 식약처 API 검색 (새로운 약물 질문 시)"""
        try:
            api_results = search_medical_data(query)
            
            if not api_results:
                return []
            
            # API 결과를 RAG 형식으로 변환
            formatted_results = []
            for doc in api_results:
                # content 필드 추가하지 말고 바로 유사도 계산
                doc_text = create_embedding_content(doc)

                # 실제 유사도 계산
                similarity = self.calculate_similarity(query, doc_text)
                
                formatted_results.append({
                    **doc,  # API 결과도 직접 필드 방식
                    "similarity_score": similarity,  
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"실시간 API 검색 실패: {e}")
            return []
        
    def calculate_similarity(self, query:str, document: str) -> float:
        """쿼리과 문서 간 코사인 유사도 계산"""
        try:
            # 쿼리 문서를 각각 임베딩
            query_embedding = self.embedder.encode([query])
            doc_embedding = self.embedder.encode([document])

            # 코사인 유사도 계산
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norm = doc_embedding / np.linalg.norm(doc_embedding)
            similarity = np.dot(query_norm, doc_norm.T)[0][0]

            return float(similarity)
        
        except Exception as e:
            print(f"유사도 계산 오류: {e}")
            return 0.0
        
    def rank_by_similarity(self, query:str, documents: List[Dict]) -> List[Dict]:
        """실시간 벡터 유사도로 문서 재순위화"""
        if not documents:
            return []
        
        scored_documents = []

        for doc in documents:
            # content 필드 대신 동적 생성
            doc_text = create_embedding_content(doc)
            similarity_score = self.calculate_similarity(query, doc_text)
            
            doc_copy = doc.copy()
            doc_copy["similarity_score"] = similarity_score
            scored_documents.append(doc_copy)
        
        # 유사도 기준으로 정렬
        scored_documents.sort(key=lambda x:x["similarity_score"], reverse=True)

        # 순위 추가
        for i, doc in enumerate(scored_documents):
            doc["rank"] = i + 1

        return scored_documents
            
    def generate_response_with_sources(self, query: str, search_results: List[Dict]) -> Dict:
        """검색 결과를 바탕으로 OpenAI로 응답 생성"""

        if not search_results:
            return {
                "response": "관련된 의료 정보를 찾을 수 없습니다.",
                "sources": [],
                "search_results": [],
                "model_used": "no_results"
            }
        
        # 검색된 문서들을 컨텍스트로 구성
        context = self._create_minimal_context(search_results, query)

        # 사용자용 완전한 소스 정보 생성
        sources_info = []
        for i, result in enumerate(search_results, 1):
            sources_info.append({
                "rank": i,
                "source": result.get("source", ""),
                "drug_name": result.get("drug_name", ""),
                "category": result.get("category", ""),
                "company_name": result.get("company_name", ""),
                "similarity": result.get("similarity_score", 0.0),
                "url": result.get("url", "")  # 사용자 클릭용 URL
            })
        
        # OpenAI 프롬프트 구성
        system_prompt = """당신은 약학 정보 제공 전문 AI야. 다음 규칙을 엄격히 준수해서 답변해줘.:

🔍 **검색 기반 응답 원칙**:
1. 제공된 문서 내용에만 기반하여 답변해줘.
2. 추천 약물이 여러가지라면 가장 흔하게 사용할 수 있는 약물(약국에서 구할 수 있는 약물)로 2가지 정도 추천해줘.
3. 약물의 전체 정보를 원하는거면 1번 응답구조로 답변하고, 특정 질문이 있다면(복용법, 최대용량 등) 그것만 대답해줘.
4. 모든 답변 끝에 "⚠️ 이 정보는 의료진 상담을 대체할 수 없습니다." 포함해줘.
5. 진단이나 처방은 절대 하지마.

# 1번 응답 구조:
💊 약물명 : \n
1. 약의 효능 (명확하게 단어로 나열해줘. 예: 콧물, 재채기, 발열)\n
2. 상세 정보
    - 용법: (약물 사용법을 알아보기 쉽게 적어줘.)
    - 최대 용량
    - 복용 시 주의사항
    - 병용법 (병용 시 주의사항이 있다면)
    - 부작용
    - 보관법

# 그외 응답 구조:
예: 1.타이레놀 얼마나 먹을 수 있어? -> 💡 최대용량 :
2. 타이레놀 먹을 때 주의할거 있어? -> 💡 복용시 주의사항 : 
"""

        user_prompt = f"""질문: {query}

참고 문서:
{context}

위 문서들을 바탕으로 정확하고 안전한 답변을 제공해줘."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1,  # 일관된 응답을 위해 낮은 temperature
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "sources": sources_info,
                "search_results": search_results,
                "model_used": "gpt-4o-mini"
            }
            
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return {
                "response": "죄송합니다. AI 응답 생성 중 오류가 발생했습니다. 검색된 정보를 확인해주세요.",
                "sources": sources_info,
                "search_results": search_results,
                "error": str(e)
            }
        
    def _create_minimal_context(self, search_results: List[Dict], query: str) -> str:
        """AI용 컨텍스트 생성"""
        
        parts = []
        
        for i, result in enumerate(search_results, 1):
            drug_name = result.get('drug_name', '')
            
            # 모든 주요 정보를 포함 (이미 압축되어 있음)
            info_parts = [f"약물: {drug_name}"]
            
            for field in ['효과', '복용법', '주의사항', '상호작용', '부작용', '보관법']:
                value = result.get(field, '')
                if value:
                    info_parts.append(f"{field}: {value}")
            
            parts.append(f"[{i}] " + " / ".join(info_parts))
        
        return "\n".join(parts)
    
    def process_query(self, query: str) -> Dict:
        """전체 RAG 파이프라인 실행"""
        
        # 1. 벡터 인덱스에서 문서 검색
        vector_results = self.search_documents(query, top_k=3)

        # 2. # 벡터 검색 결과가 부족하면 실시간 api 검색 
        low_similarity = any(result['similarity_score'] < 0.5 for result in vector_results)
        if len(vector_results) < 2 or low_similarity:
            api_results = self.search_with_api(query)

            if api_results:
                api_results = self.rank_by_similarity(query, api_results)
        else:
            api_results = []

        # 3. 결과 조합 (벡터 검색 우선, api 검색 보완)
        all_results = vector_results +  api_results
        all_results.sort(key=lambda x:x['similarity_score'], reverse=True)

        # 4. 상위 3개만 선택
        if len(all_results) > 3:
            all_results = all_results[:3]

        # 5. OpenAI로 응답 생성
        response_data = self.generate_response_with_sources(query, all_results)

        return response_data
    
# 전역 RAG 시스템 인스턴스
rag_system = None

def get_rag_system():
    """RAG 시스템 싱글톤 인스턴스 반환"""
    global rag_system
    if rag_system is None:
        rag_system = MedicalRAGSystem()
    return rag_system