import os
import json
import faiss
import time
import requests
import numpy as np
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from kfda_data_handler import get_data_handler
from embedder import UpstageEmbedder
from common_parser import item_to_documents, create_embedding_content

load_dotenv()
    
class MedicalDataBuilder:
    """의료 데이터 대량 수집 및 벡터 DB 구축"""

    def __init__(self, data_dir="./data", target_documents=5000):
        self.data_dir = data_dir
        self.target_documents = target_documents
        self.max_pages = max(100, (target_documents // 100 + 10))
        
        # 파일 경로
        self.index_path = os.path.join(data_dir, "medical_docs.index")
        self.documents_path = os.path.join(data_dir, "documents.json")
        self.progress_path = os.path.join(data_dir, "build_progress.json")
        
        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)
        
        # 임베딩 모델
        self.embedder = UpstageEmbedder(model_name="solar-embedding-1-large-passage")
        
        # 식약처 데이터 핸들러
        self.data_handler = get_data_handler()

    def load_progress(self) -> Dict:
        """이전 진행 상황 로드"""
        if os.path.exists(self.progress_path):
            with open(self.progress_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_page": 0, "total_documents": 0, "last_update": None}

    def save_progress(self, progress: Dict):
        """진행 상황 저장"""
        try:
            progress["last_update"] = datetime.now().isoformat()
            with open(self.progress_path, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"진행 상황 저장 실패: {e}")

    def collect_documents(self) -> List[Dict]:
        """페이징 방식으로 전체 약물 데이터 수집"""

        # 기존 데이터 로드
        existing_documents = []
        if os.path.exists(self.documents_path):
            try:
                with open(self.documents_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_documents = data.get('documents', [])
            except Exception as e:
                print(f"기존 데이터 로드 실패: {e}")
        
        # 진행 상황 로드
        progress = self.load_progress()
        start_page = progress.get("last_page", 0) + 1
        
        all_documents = existing_documents.copy()  # 기존 데이터 복사
        page = start_page  # 마지막 페이지부터 시작

        while page <= self.max_pages:
            try:

                params = {
                    'serviceKey': self.data_handler.api_key,
                    'numOfRows': 100,
                    'pageNo': page,
                    'type': 'json'
                }

                response = requests.get(self.data_handler.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                # API 응답 검증
                header = data.get('header', {})
                if header.get('resultCode') != '00':
                    print(f"API 오류: {header.get('resultMsg')}")
                    break
                    
                items = data.get('body', {}).get('items', [])

                # 응답 형식 정규화
                if isinstance(items, dict):
                    items = [items]
                elif not isinstance(items, list):
                    items = []
                
                if not items:
                    print(f"페이지 {page}: 데이터 없음 - 수집 완료")
                    break

                # 각 약물 문서로 반환
                page_documents = []
                for item in items:
                    docs = self._item_to_documents(item)
                    page_documents.extend(docs)

                all_documents.extend(page_documents)

                # 페이지 업데이트  -> 마지막에만 하면 중간 실패시 날아감.
                progress["last_page"] = page
                progress["total_documents"] = len(all_documents)
                self.save_progress(progress)

                if len(all_documents) >= self.target_documents:
                    print(f"목표 달성: {len(all_documents)}개 완료")
                    break

                page +=1
                time.sleep(0.5)
            
            except Exception as e:
                print(f"페이지 {page} 실패: {e}")

                # 진행 상황 저장
                progress["last_page"] = page -1  # 실패한 페이지는 제외
                progress["total_documents"] = len(all_documents)
                self.save_progress(progress)

                time.sleep(0.5)
                page += 1

        unique_documents = self._remove_duplicates(all_documents)
        
        return unique_documents
    

    def _item_to_documents(self, item: Dict) -> List[Dict]:
        """API 응답 아이템을 문서로 변환"""
        return item_to_documents(item)

    def _remove_duplicates(self, documents: List[Dict]) -> List[Dict]:
        """약물명 기준으로 중복 제거 (같은 약물은 하나만)"""
        
        unique_documents = []
        seen_drugs = set() 
        # duplicate_examples = []
        
        for doc in documents:
            # 약물명 + 카테고리 + 회사명으로 고유 키 생성
            drug_key = f"{doc['product_name']}_{doc['category']}_{doc['company_name']}"

            if drug_key not in seen_drugs:
                seen_drugs.add(drug_key)
                unique_documents.append(doc)

        return unique_documents
    
    def build_vector_index(self, documents: List[Dict]):
        """벡터 인덱스 구축 및 저장"""
        
        if not documents:
            print("문서가 없어 인덱스를 구축할 수 없습니다.")
            return
        
        # 임베딩 생성
        contents = []

        for i, doc in enumerate(documents):
            embeddings_text = create_embedding_content(doc)
            contents.append(embeddings_text)
        
        # 배치 처리로 메모리 효율성 증대
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(contents), batch_size):
            batch = contents[i:i+batch_size]
            batch_embeddings = self.embedder.encode(batch)
            all_embeddings.append(batch_embeddings)
    
        # 임베딩 합치기
        embeddings = np.concatenate(all_embeddings, axis=0)

        # FAISS 인덱스 생성
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)

        # L2 정규화 후 추가
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))

        # FAISS 인덱스 저장
        faiss.write_index(index, self.index_path)

        # 문서 저장
        data = {
            'documents': documents,
            'build_date': datetime.now().isoformat(),
            'total_documents': len(documents),
            'embedding_model': 'solar-embedding-1-large-passage',
            'document_format': 'direct_fields',  # 새로운 포맷 표시
            'field_structure': [
                '효과',
                '복용법', 
                '주의_금기사항',
                '상호작용_병용',
                '부작용',
                '보관법'
            ]
        }

        with open(self.documents_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def build_full_database(self):
        """전체 데이터베이스 구축 프로세스"""

        try:
            # 1. 문서 수집
            documents = self.collect_documents()

            # 2. 벡터 인덱스 구축
            self.build_vector_index(documents)

        except KeyboardInterrupt:
            print("\n사용자가 중단했습니다.")
            print("진행 상황이 저장되었습니다. 다시 실행하면 이어서 진행됩니다.")
        except Exception as e:
            print(f"\n오류 발생: {e}")
            print("진행 상황이 저장되었습니다.")

def main():
    """메인 실행"""
    print("의료 데이터 수집 및 벡터 DB 구축 도구")
    print("주의: 이 과정은 30분-2시간 정도 소요됩니다.")

    response = input("\n계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    

    try:
        target = input(f"\n목표 문서 수를 입력하세요 (기본값: 5000): ").strip()
        target_documents = int(target) if target else 5000

    except ValueError:
        target_documents = 5000

    print(f"목표 문서 수: {target_documents}")

    # 데이터 빌더 실행
    builder = MedicalDataBuilder(target_documents=target_documents)
    builder.build_full_database()

if __name__ == "__main__":
    main()







