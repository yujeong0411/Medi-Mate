import os
import json
import faiss
import numpy as np
import urllib.parse
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from kfda_data_handler import get_data_handler, search_medical_data
from direct_embedder import DirectEmbedder

# Responses API가 새로 나왔지만, 안정성을 위해 Chat Completions API 사용

load_dotenv()

class MedicalRAGSystem:
    """영구 저장 가능한 FAISS 기반 RAG 시스템"""

    def __init__(self, data_dir="./data"):
        # 경로 설정
        self.data_dir = data_dir
        self.index_path = os.path.join(data_dir, "medical_docs.index")
        self.documents_path = os.path.join(data_dir, "documents.json")
        self.last_update_path = os.path.join(data_dir, "last_update.txt")

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

        # OPENAI 설정
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 임베딩 모델
        print("한국어 임베딩 모델 로딩 중...")
        self.embedder = DirectEmbedder('jhgan/ko-sroberta-multitask')
        print("임베딩 모델 로드 완료")

        # 식약처 데이터 핸들러
        self.data_handler = get_data_handler()

        # FAISS 인덱스와 메타데이터
        self.index = None
        self.documents = []

        # 시스템 초기화
        self._initialize_system()

        print("RAG 시스템 초기화 완료")

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
        """기존 인덱스와 메타데이터 로드"""

        try:
            if os.path.exists(self.index_path) and os.path.exists(self.documents_path):
                # FAISS 인덱스 로드
                self.index = faiss.read_index(self.index_path)
                
                # 메타데이터 로드
                with open(self.documents_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data['documents']
                
                print(f"기존 데이터 로드: {len(self.documents)}개 문서")
                return True
                
        except Exception as e:
            print(f"기존 인덱스 로드 실패: {e}")

        return False

    def _rebuild_index(self, documents: List[Dict]):
        """인덱스 재구축"""
        print(f"{len(documents)}개 문서로 FAISS 인덱스 구축 중...")
        
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
        print("FAISS 인덱스 구축 완료")

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
                
            print("디스크 저장 완료")
            
        except Exception as e:
            print(f"디스크 저장 실패: {e}")
            
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """쿼리와 유사한 문서 검색 - 벡터 검색"""
        if self.index is None:
            print("검색 인덱스가 없습니다.")
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
                    "content": doc["content"],  # 실제 텍스트 내용
                    "source": {  # 출처 정보 구조화
                        "source": doc["source"],
                        "drug_name": doc["drug_name"],
                        "category": doc["category"],
                        "url": doc.get("url", ""),
                        "company_name": doc.get("company_name", "")
                    },
                    "similarity_score": float(score),
                    "rank": i + 1
                })
        
        return results

    def search_with_api(self, query: str) -> List[Dict]:
        """실시간 식약처 API 검색 (새로운 약물 질문 시)"""
        try:
            print(f"실시간 식약처 API 검색: '{query}'")
            api_results = search_medical_data(query)
            
            if not api_results:
                return []
            
            # API 결과를 RAG 형식으로 변환
            formatted_results = []
            for doc in api_results:
                formatted_results.append({
                    "content": doc["content"],
                    "source": {
                        "source": doc["source"],
                        "drug_name": doc["drug_name"],
                        "category": doc["category"],
                        "url": doc.get("url", ""),
                        "company_name": doc.get("company_name", "")
                    },
                    "similarity_score": 0.9,  # API 검색은 높은 점수
                    "rank": len(formatted_results) + 1
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
        
        print("벡터 유사도 계산 중...")
        scored_documents = []

        for doc in documents:
            similarity_score = self.calculate_similarity(query, doc["content"])
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
        context = ""
        sources_info = []
        
        for i, result in enumerate(search_results, 1):
            source_info = result['source']
            context += f"\n[문서 {i}] {result['content']}\n"
            context += f"출처: {source_info['source']}\n"
            context += f"약물: {source_info['drug_name']}\n"
            context += f"카테고리: {source_info['category']}\n"
           
            sources_info.append({
                "rank": i,
                "source": source_info['source'],
                "drug_name": source_info['drug_name'],
                "category": source_info['category'],
                "company_name": source_info.get('company_name', ''),
                "similarity": result['similarity_score'],
                "url": f"https://nedrug.mfds.go.kr/search?keyword={urllib.parse.quote(source_info['drug_name'])}"
            })

            # 🔍 디버깅용 출력
            print(f"🔗 생성된 URL: https://nedrug.mfds.go.kr/search?keyword={urllib.parse.quote(source_info['drug_name'])}")
        
        # OpenAI 프롬프트 구성
        system_prompt = """당신은 약학 정보 제공 전문 AI야. 다음 규칙을 엄격히 준수해서 답변해줘.:

🔍 **검색 기반 응답 원칙**:
1. 제공된 문서 내용에만 기반하여 답변해줘.
2. 추천 약물은 가장 흔하게 사용할 수 있는 약물(약국에서 구할 수 있는 약물)로 추천해줘.
3. 검색이 나왔으면 추천 약물명이 무조건 있어야해. 추천 약물이 없다면 모든 답변을 할 수가 없어.
4. 사용자가 약물을 검색했다면 1번 응답 구조로 답변하고, 사용자가 약물명을 제외하고 검색했다면 2번 응답으로 답변해줘.
5. 모든 의학적 정보는 중복을 제거해서 반드시 출처를 명해줘.
6. 응급상황(뇌졸중, 심근경색 등 의심스러운 증상) 시 즉시 119 연락 및 병원 방문을 권해줘.
7. 사람들이 한 눈에 알아보기 쉽게 설명해줘. 
8. 만약 추천 약물을 적을 수 없다면, 그냥 찾을 수 없다고 말해줘.
9. 모든 답변 끝에 "⚠️ 이 정보는 의료진 상담을 대체할 수 없습니다." 포함해줘.
10. 진단이나 처방은 절대 하지마.

# 1번 응답 구조:
💊 검색 약물 : (검색 약물명)\n
1. 약의 효능 (명확하게 단어로 나열해줘. 예: 콧물, 재채기, 발열)\n
2. 상세 정보
    - 용법: (약물 사용법을 알아보기 쉽게 적어줘.)
    - 최대 용량
    - 복용 시 주의사항
    - 부작용
    - 보관법

# 2번 응답 구조:
💊 증상 : (사용자가 입력한 증상을 가능하면 전문용어로 요약해서 적어줘. 예: 머리가 아파 -> 두통)\n
1. 추천 약물: (추천 약물명: 무조건 있어야해. 만약 없다면 나머지도 답변할 수가 없는거야.)\n
2. 약의 효능: (명확하게 단어로 나열해줘. 예: 콧물, 재채기, 발열)\n
3. 상세 정보
    - 용법: (약물 사용법을 알아보기 쉽게 적어줘.)
    - 최대 용량
    - 복용 시 주의사항
    - 부작용
    - 보관법
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
                max_tokens=800,
                temperature=0.1  # 일관된 응답을 위해 낮은 temperature
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "sources": sources_info,
                "search_results": search_results,
                "model_used": "gpt-4o-mini",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return {
                "response": "죄송합니다. AI 응답 생성 중 오류가 발생했습니다. 검색된 정보를 확인해주세요.",
                "sources": sources_info,
                "search_results": search_results,
                "error": str(e)
            }
    
    def process_query(self, query: str) -> Dict:
        """전체 RAG 파이프라인 실행"""
        
        # 1. 벡터 인덱스에서 문서 검색
        vector_results = self.search_documents(query, top_k=3)

        # 2. # 벡터 검색 결과가 부족하면 실시간 api 검색 
        api_results = []
        # if len(vector_results) < 2:   
        #     api_results = self.search_with_api(query)
        #     # 실시간 검색 결과도 유사도로 재순위화
        #     api_results = self.rank_by_similarity(query, api_results) 
        # 유사도 0.7 이하이거나 결과가 2개 미만이면 API 검색
        
        low_similarity = any(result['similarity_score'] < 0.7 for result in vector_results)
        if len(vector_results) < 2 or low_similarity:
            print(f"🌐 API 검색 트리거: 벡터결과={len(vector_results)}, 낮은유사도={low_similarity}")
            api_results = self.search_with_api(query)
            api_results = self.rank_by_similarity(query, api_results) 

        # 3. 결과 조합 (벡터 검색 우선, api 검색 보완)
        all_results = vector_results +  api_results

        # 4. 상위 3개만 선택
        if len(all_results) > 3:
            all_results = all_results[:3]
            
        # 5. 순위 재조정
        for i, result in enumerate(all_results):
            result['rank'] = i + 1
        
        if not all_results:
            return {
                "response": "관련된 의료 정보를 찾을 수 없습니다. 다른 약물명이나 질문으로 시도해보세요.",
                "sources": [],
                "search_results": [],
                "model_used": "no_results"
            }
        
        # 6. OpenAI로 응답 생성
        response_data = self.generate_response_with_sources(query, all_results)
        
        print(f"검색 완료: 벡터 {len(vector_results)}개 + API {len(api_results)}개")

        return response_data
    
# 전역 RAG 시스템 인스턴스
rag_system = None

def get_rag_system():
    """RAG 시스템 싱글톤 인스턴스 반환"""
    global rag_system
    if rag_system is None:
        print("RAG 시스템 초기화 중...")
        rag_system = MedicalRAGSystem()
        print("RAG 시스템 초기화 완료")
    return rag_system