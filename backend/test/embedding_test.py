# 1. 필요한 라이브러리 설치 -> colab이나 jupyter로 하는걸 추천
# pip install sentence-transformers torch upstage

# 실행 결과에서 확인할 점
# Positive 평균: 유사한 쿼리쌍일수록 높아야 함 (0.7~1.0 이상 기대)
# Negative 평균: 무관한 쿼리는 낮아야 함 (0.0~0.3 기대)
# Margin: 두 값의 차이가 클수록 모델이 분별을 잘한다는 뜻

# 2. 업스테이지 API 키 설정
import os
os.environ["UPSTAGE_API_KEY"] = "YOUR_API_KEY"  # 여기에 실제 API 키 입력

from sentence_transformers import SentenceTransformer, util
import numpy as np
from upstage import Upstage

# SentenceTransformer 방식 모델들
sentence_transformer_models = [
    "jhgan/ko-sbert-nli",
    "snunlp/KR-SBERT-V40K-klueNLI-augSTS",
    "deliciouscat/kf-deberta-base-cross-sts",
    "upskyy/kf-deberta-multitask",
]

# 업스테이지 API 방식 모델들
upstage_models = [
    "solar-embedding-1-large-query",
    "solar-embedding-1-large-passage"
]

# 테스트용 쿼리쌍
test_queries = [
    ("타이레놀 용량", "아세트아미노펜 복용법"),  # Positive
    ("두통약", "진통제"),                     # Positive
    ("임신 중 약물", "임산부 금기 약물"),      # Positive
    ("항생제 내성", "피부 보습제")            # Negative
]

def evaluate_sentence_transformer_model(model_name):
    try:
        model = SentenceTransformer(model_name)
        pos_scores, neg_scores = [], []

        print(f"🔍 {model_name} 평가 중...")
        
        for a, b in test_queries:
            emb1 = model.encode(a, convert_to_tensor=True)
            emb2 = model.encode(b, convert_to_tensor=True)
            score = util.cos_sim(emb1, emb2).item()
            
            if (a, b) == ("항생제 내성", "피부 보습제"):
                neg_scores.append(score)
            else:
                pos_scores.append(score)
            print(f"  {a} vs {b} → 유사도 {score:.3f}")

        return calculate_results(model_name, pos_scores, neg_scores)
        
    except Exception as e:
        print(f"❌ {model_name} 로드 실패: {e}")
        print("="*60, "\n")
        return None

def evaluate_upstage_model(model_name):
    try:
        client = Upstage()
        pos_scores, neg_scores = [], []

        print(f"🔍 upstage/{model_name} 평가 중...")
        
        for a, b in test_queries:
            # 업스테이지 API로 임베딩 생성
            emb1 = client.embeddings.create(model=model_name, input=a).data[0].embedding
            emb2 = client.embeddings.create(model=model_name, input=b).data[0].embedding
            
            # 코사인 유사도 계산
            emb1 = np.array(emb1)
            emb2 = np.array(emb2)
            score = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            if (a, b) == ("항생제 내성", "피부 보습제"):
                neg_scores.append(score)
            else:
                pos_scores.append(score)
            print(f"  {a} vs {b} → 유사도 {score:.3f}")

        return calculate_results(f"upstage/{model_name}", pos_scores, neg_scores)
        
    except Exception as e:
        print(f"❌ upstage/{model_name} 로드 실패: {e}")
        print("="*60, "\n")
        return None

def calculate_results(model_name, pos_scores, neg_scores):
    pos_avg = sum(pos_scores) / len(pos_scores)
    neg_avg = sum(neg_scores) / len(neg_scores)
    margin = pos_avg - neg_avg
    
    print(f"\n📊 {model_name} 성능 요약")
    print(f"- Positive 평균: {pos_avg:.3f}")
    print(f"- Negative 평균: {neg_avg:.3f}")
    print(f"- Margin (구분력): {margin:.3f}")
    
    # 성능 등급 매기기
    if margin > 0.4:
        grade = "🟢 우수"
    elif margin > 0.2:
        grade = "🟡 보통"
    else:
        grade = "🔴 개선필요"
    print(f"- 성능 등급: {grade}")
    print("="*60, "\n")
    
    return {"model": model_name, "pos_avg": pos_avg, "neg_avg": neg_avg, "margin": margin}

# 모든 모델 평가 실행
results = []

# SentenceTransformer 모델들 평가
for m in sentence_transformer_models:
    result = evaluate_sentence_transformer_model(m)
    if result:
        results.append(result)

# 업스테이지 모델들 평가
for m in upstage_models:
    result = evaluate_upstage_model(m)
    if result:
        results.append(result)

# 최종 순위 출력
if results:
    print("\n🏆 모델 성능 순위 (Margin 기준)")
    print("-" * 60)
    sorted_results = sorted(results, key=lambda x: x['margin'], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}위: {result['model']}")
        print(f"     Margin: {result['margin']:.3f} (Pos: {result['pos_avg']:.3f}, Neg: {result['neg_avg']:.3f})")
        print()

print("\n💡 참고사항:")
print("- solar-embedding-1-large-query: 검색 쿼리에 최적화 (업스테이지)")
print("- solar-embedding-1-large-passage: 긴 문서/패시지에 최적화 (업스테이지)")
print("- 업스테이지 모델은 API 호출 방식으로 동작합니다")