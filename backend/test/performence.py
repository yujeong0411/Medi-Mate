from kfda_data_handler import get_data_handler

def test_keyword_extraction():
    """키워드 추출 성능 실제 테스트"""
    
    # 데이터 핸들러 로드 (키워드 추출기 포함)
    print("🔧 키워드 추출 시스템 로드 중...")
    data_handler = get_data_handler()
    
    test_cases = [
        {
            "query": "타이레놀 복용법 알려줘",
            "description": "명확한 약물명 포함"
        },
        {
            "query": "임신 중 머리 아픈데 뭐 먹을까?",
            "description": "증상 기반 질문"
        },
        {
            "query": "감기약과 진통제 같이 먹어도 돼?",
            "description": "상호작용 문의"
        },
        {
            "query": "아세트아미노펜 하루 최대 용량은?",
            "description": "성분명 사용"
        },
        {
            "query": "몸살감기에 좋은 약 추천해줘",
            "description": "모호한 증상 표현"
        }
    ]
    
    print("🧪 키워드 추출 정확도 테스트")
    print("=" * 50)
    
    successful_extractions = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        description = test["description"]
        
        print(f"\n{i}. {description}")
        print(f"   쿼리: {query}")
        
        try:
            # 실제 키워드 추출 실행
            drugs, symptoms, intent = data_handler.keyword_extractor.extract_search_keywords(query)
            
            print(f"   📋 추출된 약물: {drugs}")
            print(f"   🏥 추출된 증상: {symptoms}")
            print(f"   🎯 분류된 의도: {intent}")
            
            # 성공 여부 판단 (추출된 내용이 있으면 성공)
            if drugs or symptoms or intent != "general":
                successful_extractions += 1
                print("   ✅ 성공적 추출")
            else:
                print("   ❌ 추출 실패")
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
    
    # 성공률 계산
    success_rate = (successful_extractions / len(test_cases)) * 100
    print(f"\n📊 키워드 추출 성공률: {successful_extractions}/{len(test_cases)} ({success_rate:.1f}%)")

# 실행하려면:
test_keyword_extraction()