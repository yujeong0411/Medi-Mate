import time
from rag_system import get_rag_system

def measure_system_performance():
    """실제 시스템 성능 측정"""
    rag = get_rag_system()
    
    test_queries = [
        "타이레놀 복용법 알려줘",
        "임신 중 머리 아픈데 뭐 먹을까?",
        "감기약과 진통제 같이 먹어도 돼?",
        "애드빌 부작용 있어?",
        "낙센 하루에 몇 번 먹어?"
    ]

    print("📊 실제 성능 측정 시작")
    print("=" * 50)
    
    total_time = 0
    vector_only_count = 0
    api_needed_count = 0
    
    print("📊 실제 성능 측정 결과")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 테스트 쿼리: {query}")
        
        try:
            start_time = time.time()
            result = rag.process_query(query)
            response_time = time.time() - start_time
            
            total_time += response_time
            
            # 검색 방식 확인
            sources = result.get('sources', [])
            has_api_results = any('api' in str(source) for source in sources)
            
            if has_api_results:
                api_needed_count += 1
                search_type = "벡터 + API"
            else:
                vector_only_count += 1
                search_type = "벡터만"
            
            print(f"   응답 시간: {response_time:.2f}초")
            print(f"   검색 방식: {search_type}")
            print(f"   소스 수: {len(sources)}개")

            # 응답 일부 출력
            response_preview = result.get('response', '')[:100] + "..."
            print(f"   💬 응답 미리보기: {response_preview}")
            
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
    
    # 종합 결과
    if total_time > 0:
        avg_time = total_time / len(test_queries)
        print(f"\n📈 종합 결과:")
        print(f"   평균 응답시간: {avg_time:.2f}초")
        print(f"   벡터 검색만: {vector_only_count}/{len(test_queries)}개")
        print(f"   API 보완 필요: {api_needed_count}/{len(test_queries)}개")

# 실행
measure_system_performance()