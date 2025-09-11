import os
import json

def check_system_resources():
    """시스템 리소스 사용량 확인"""
    
    print("💾 시스템 리소스 현황")
    print("=" * 40)
    
    # 파일 크기 확인
    data_dir = "./data"
    files_to_check = [
        ("FAISS 인덱스", "medical_docs.index"),
        ("문서 메타데이터", "documents.json"),
        ("진행률 파일", "build_progress.json")
    ]
    
    total_size = 0
    
    for name, filename in files_to_check:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            size_mb = size / (1024 * 1024)
            total_size += size
            print(f"📁 {name}: {size_mb:.1f} MB")
        else:
            print(f"📁 {name}: 파일 없음")
    
    total_mb = total_size / (1024 * 1024)
    print(f"📊 총 사용 용량: {total_mb:.1f} MB")
    
    # 문서 통계 (documents.json이 있는 경우)
    documents_path = os.path.join(data_dir, "documents.json")
    if os.path.exists(documents_path):
        try:
            with open(documents_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data.get('documents', [])
                
            print(f"\n📚 데이터베이스 통계:")
            print(f"   총 문서 수: {len(documents)}개")
            print(f"   구축 일시: {data.get('build_date', '미상')}")
            print(f"   임베딩 모델: {data.get('embedding_model', '미상')}")
            
            # 카테고리별 분포 (상위 5개)
            if documents:
                categories = {}
                for doc in documents:
                    category = doc.get('category', '미분류')
                    categories[category] = categories.get(category, 0) + 1
                
                print(f"\n📊 카테고리별 문서 분포 (상위 5개):")
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                for category, count in sorted_categories[:5]:
                    percentage = (count / len(documents)) * 100
                    print(f"   {category}: {count}개 ({percentage:.1f}%)")
                    
        except Exception as e:
            print(f"❌ 문서 통계 확인 실패: {e}")
    else:
        print("\n❌ documents.json 파일이 없습니다.")

# 실행하려면:
check_system_resources()