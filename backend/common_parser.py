import re
from typing import List, Dict

def item_to_documents(item: Dict, search_drug: str = None) -> List[Dict]:
        """API 응답 아이템을 문서로 변환"""

        documents = []
        product_name = item.get('itemName', '').strip()
        company_name = item.get('entpName', '').strip()

        if not product_name:
            return documents
        
        # API 필드 매핑
        field_mapping = {
            'efcyQesitm': '효능',
            'useMethodQesitm': '사용법',
            'atpnWarnQesitm': '주의사항경고',
            'atpnQesitm': '주의사항',
            'intrcQesitm': '상호작용',
            'seQesitm': '부작용',
            'depositMethodQesitm': '보관법'
        }

        for field_name, category in field_mapping.items():
            content = item.get(field_name, '')

            if is_valid_content(content):
                cleaned_content = clean_text(content)

                if len(cleaned_content) > 15:
                    documents.append({
                        "content": cleaned_content,
                        "source": f"식약처 의약품개요정보 - {product_name}",
                        "drug_name": search_drug or product_name,
                        "product_name": product_name,
                        "company_name": company_name,
                        "category": category,
                        "url": "https://nedrug.mfds.go.kr"
                    })

        return documents

def is_valid_content(content: str) -> bool:
    """유효한 내용인지 확인"""
    # null 값 체크
    if content is None:
        return False
        
    if not content or not isinstance(content, str):
        return False
    
    content = content.strip()
    if len(content) < 4:
        return False
    
    # 의미 없는 텍스트 패턴
    meaningless = ['해당없음', '없음', '-', 'N/A', '정보없음']
    content_lower = content.lower()

    for pattern in meaningless:
        if pattern.lower() in content_lower:
            return False
        
    return True

def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""
    
    # HTML 제거
    text = re.sub(r'<[^>]+>', '', text)

    # HTML 엔티티 변환
    # '&nbsp;'  Non-Breaking Space → 공백 (' ')
    # '&lt;'     Less Than → '<' 기호
    # '&gt;'     Greater Than → '>' 기호  
    # '&amp;'    Ampersand → '&' 기호
    # '&quot;'   Quotation → '"' 기호
    # '&#39;'    Apostrophe → "'" 기호
    replacements = {
        '&nbsp;': ' ', '&lt;': '<', '&gt;': '>',
        '&amp;': '&', '&quot;': '"', '&#39;': "'"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # 공백 처리
    text = re.sub(r'\s+', ' ', text)

    return text.strip()