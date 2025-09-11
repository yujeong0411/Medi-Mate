import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from common_parser import item_to_documents
from keyword_extractor import OpenAIKeywordExtractor

load_dotenv()

class KFDADataHandler:
    """식약처 API 데이터 처리 클래스"""

    def __init__(self):
        self.api_key = os.getenv("KFDA_API_KEY")
        self.base_url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"

        # OpenAI 클라이언트 (RAG 시스템과 공유)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.keyword_extractor = OpenAIKeywordExtractor(self.openai_client)

        if not self.api_key:
            raise ValueError("🔑 KFDA_API_KEY가 필요합니다. .env 파일에 설정하세요.")

    def search_drug(self, query: str) -> List[Dict]:
        """API에서 약명과 증상으로 검색하는 통합 함수"""

        # 1. AI로 키워드 추출
        drug_names, symptoms, intent = self.keyword_extractor.extract_search_keywords(query)

        all_documents = []

        # 2. 추출된 키워드로 검색
        # 약물명 검색
        for drug_name in drug_names:
            try:
                drug_docs = self._search_by_drug_name(drug_name)
                all_documents.extend(drug_docs)

            except Exception as e:
                print(f"❌ 약물 '{drug_name}' 검색 실패: {e}")
        
        # 증상 검색  
        for symptom in symptoms:
            try:
                symptom_docs = self._search_by_symptom(symptom)
                all_documents.extend(symptom_docs)

            except Exception as e:
                print(f"❌ 증상 '{symptom}' 검색 실패: {e}")

        # 3. 키워드가 없으면 원본 쿼리로 폴백
        if not drug_names and not symptoms:
            try:
                fallback_docs = self._search_by_drug_name(query)
                all_documents.extend(fallback_docs)
            except:
                pass
            
        # 중복 제거
        unique_docs = []
        seen_products = set()

        for doc in all_documents:
            product_key = f"{doc['product_name']}_{doc['category']}"
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_docs.append(doc)

        return unique_docs
    
    def _search_by_drug_name(self, drug_name: str) -> List[Dict]:
        """약명으로 검색"""
        
        params = {
            'serviceKey' :  self.api_key,
            'itemName' : drug_name,
            'numOfRows': 3,
            'pageNo': 1,
            'type' : 'json'
        }

        return self._api_call(params, drug_name)
    
    def _search_by_symptom(self, symptom:str) -> List[Dict]:
        """증상으로 검색"""

        params = {
            'serviceKey' :  self.api_key,
            'efcyQesitm' : symptom,
            'numOfRows': 3,
            'pageNo': 1,
            'type' : 'json'
        }

        return self._api_call(params, symptom)
    
    def _api_call(self, params: Dict, search_term: str) -> List[Dict]:
        """공통 API 호출 로직"""

        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()  # 문자열으로 오기때문에 json으로 변환

        # API 응답 검증
        header = data.get('header', {})
        if header.get('resultCode') != '00':
            return []
        
        items = data.get('body', {}).get('items', [])

        # items 처리 : 응답이 1개일땐 dict, 없으면 빈 문자열로 오기때문에 전부다 list로 변환
        if isinstance(items, dict):
            items = [items]
        elif not isinstance(items, list):
            items = []

        # 문서 변환
        documents = []
        for item in items:
            docs = self._item_to_documents(item, search_term)
            documents.extend(docs)

        return documents
    
    def _item_to_documents(self, item:Dict, search_drug: str) -> List[Dict]:
        return item_to_documents(item, search_drug)
    
# 전역 인스턴스
_data_handler = None

def get_data_handler():
    """데이터 핸들러 싱글톤 반환"""
    global _data_handler
    if _data_handler is None:
        _data_handler = KFDADataHandler()
    return _data_handler

def get_medical_documents():
    """의료 문서 가져오기"""
    return get_data_handler().get_medical_documents()

def search_medical_data(query: str):
    """사용자 쿼리로 의료 데이터 검색 (약명+증상)"""
    return get_data_handler().search_drug(query)

