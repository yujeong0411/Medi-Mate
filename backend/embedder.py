import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# solar-embedding-1-large-query :질문(쿼리) 임베딩 전용
# 사용자의 검색 질의문 같은 짧은 텍스트 최적화
# 데이터 구축 시 (data_builder.py → 문서 인덱싱)

# solar-embedding-1-large-passage :문서(패시지) 임베딩 전용
# 긴 텍스트(설명, 약품 정보, 가이드라인) 최적화
# 실시간 검색 시 (rag_system.py → 사용자 쿼리)

class UpstageEmbedder:
    """Upstage 임베딩 (OpenAI SDK 호환)"""

    def __init__(self, model_name="solar-embedding-1-large-passage"):
        self.model_name = model_name
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("❌ UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1"
        )

    def encode(self, texts):
        """텍스트를 벡터로 변환"""
        if isinstance(texts, str):
            texts = [texts]

        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )

        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings, dtype="float32")