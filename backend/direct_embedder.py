import torch
from transformers import AutoTokenizer, AutoModel

class DirectEmbedder:
    """sentence-transformers와 openai 호환성 충돌로 직접 구현 임베딩"""
    
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        print(f"임베딩 모델 로딩 중: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()  # 평가 모드
        print("임베딩 모델 로드 완료")

    def encode(self, texts):
        """텍스트를 벡터로 변환"""
        if isinstance(texts, str):
            texts = [texts]

        # 토큰화
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors='pt',
            max_length=512
        )

        # 임베딩 생성
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 평균 풀링 (sentence-transformers와 동일한 방식)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.numpy()