from rag_system import get_rag_system
import time

def test_hybrid_search_effectiveness():
    """하이브리드 검색 효과 측정"""
    
    print("🔄 하이브리드 검색 효과 테스트")
    print("=" * 50)
    
    # RAG 시스템 로드
    rag = get_rag_system()
    
    # 다양한 유형의 테스트 쿼리
    test_scenarios = [
        {
            "query": "타이레놀",
            "type": "일반적인 약물명",
            "expected": "벡터 검색으로 충분"
        },
        {
            "query": "2024년 신약 코로나 치료제",
            "type": "최신 정보",
            "expected": "API 검색 필요"
        },
        {
            "query": "머리아픈데 임신중이라 뭐먹지",
            "type": "복합 질문",
            "expected": "하이브리드 검색 효과적"
        },
        {
            "query": "qwerty12345",
            "type": "무의미한 쿼리",
            "expected": "검색 실패 예상"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        query = scenario["query"]
        query_type = scenario["type"]
        expected = scenario["expected"]
        
        print(f"\n{i}. {query_type} 테스트")
        print(f"   쿼리: {query}")
        print(f"   예상: {expected}")
        
        try:
            result = rag.process_query(query)
            
            sources = result.get('sources', [])
            response = result.get('response', '')
            
            if sources:
                # 첫 번째 소스의 유형 확인
                first_source = sources[0]
                source_info = first_source.get('source', '')
                print(f"   📋 주요 소스: {source_info[:50]}...")
            else:
                print(f"   ❌ 검색 실패")
            
            # 응답 품질 간단 평가
            if len(response) > 50:
                print(f"   💬 응답 품질: 양호")
            else:
                print(f"   💬 응답 품질: 부족")
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
    
    print(f"\n📋 테스트 완료. 위 결과를 통해 하이브리드 검색의 효과를 확인할 수 있습니다.")

# 실행하려면:
test_hybrid_search_effectiveness()