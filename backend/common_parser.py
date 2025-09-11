import re
import urllib.parse
from typing import List, Dict

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

def extract_core_effects(text: str) -> str:
    """효능에서 핵심 질환/증상 패턴만 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    # 질환/증상 패턴들을 정규식으로 추출
    patterns = [
        r'[가-힣]{2,}증',          # ~증 (기능무력증, 결핍증 등)
        r'[가-힣]{2,}염',          # ~염 (기관지염, 위염 등) 
        r'[가-힣]{2,}통',          # ~통 (근육통, 관절통 등)
        r'[가-힣]{2,}불량',        # ~불량 (소화불량 등)
        r'[가-힣]{2,}장애',        # ~장애 (순환장애 등)
        r'[가-힣]{2,}중독',        # ~중독 (약물중독 등)
        r'습진|피부염|화상|열상',   # 피부 관련
        r'객담|가래|기침',         # 호흡기 관련
        r'변비|설사|구토|구역',     # 소화기 관련
        r'진통|소염|항염',         # 치료 효과
        r'[가-힣]{2,}저림',     # 수족저림 등
        r'[가-힣]{2,}냉증',     # 수족냉증 등  
        r'[가-힣]{2,}부전',     # 분비부전 등
        r'비타민\s*[A-Z].*?결핍증',  # 비타민 결핍증
        r'순환.*?장애',        # 순환장애
    ]
    
    found_terms = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found_terms.extend(matches)
    
    if found_terms:
        # 중복 제거하고 최대 5개
        unique_terms = list(dict.fromkeys(found_terms))[:5]
        return ", ".join(unique_terms)
    else:
        # 패턴 매칭 실패시 첫 문장의 핵심 부분만
        cleaned = re.sub(r'이 약은\s*', '', text)
        cleaned = re.sub(r'에 사용합니다.*', '', cleaned)
        return cleaned.strip()[:50]

def extract_core_dosage(text: str) -> str:
    """복용법에서 핵심 용법 패턴만 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    results = []
    
    # 성인 용법 패턴 
    adult_patterns = [
        r'성인.*?(1회\s*[\d~.-]+[가-힣mgml]*.*?\d+일\s*\d+회)',
        r'성인.*?(\d+일\s*\d+회.*?[\d~.-]+[가-힣mgml]*)',
        r'성인.*?(1회\s*[\d~.-]+[가-힣mgml/]*(?:\s*씩)?)',  # "1회 1포씩" 추가
        r'성인.*?(\d+일\s*\d+[~-]?\d*[매정포캡슐방울mlmg])',

    ]
    
    for pattern in adult_patterns:
        match = re.search(pattern, text)
        if match:
            dosage = re.sub(r'\s+', ' ', match.group(1)).strip()
            results.append(f"성인 {dosage}")
            break
    
    # 소아/어린이 용법 패턴
    child_patterns = [
        r'(소아|어린이|유아).*?(\d+세.*?\d+[회매정포mlmg].*?\d+[가-힣]*)',
        r'(\d+세\s*이상.*?\d+[회매정포mlmg].*?\d+[가-힣]*)',
        r'(\d+세\s*미만.*?\d+[회매정포mlmg].*?\d+[가-힣]*)',
        r'(만\s*\d+세.*?1회.*?[\d/]+[가-힣mgml]*)'
    ]
    
    for pattern in child_patterns:
        match = re.search(pattern, text)
        if match:
            dosage = re.sub(r'\s+', ' ', match.group().strip())
            results.append(dosage)
            break

    # 일반적인 용법 패턴 (성인 표기가 없는 경우)
    if not results:  # 성인/소아 패턴이 없을 때만
        general_patterns = [
            r'1일\s*\d+[~-]?\d*회.*?환부',
            r'1회\s*\d+[~-]?\d*방울.*?\d+일\s*\d+회',
            r'1일\s*수회.*?환부',
            r'1일\s*\d+[~-]?\d*회.*?적당량',
            r'1일\s*\d+[~-]?\d*회.*?환부.*?붙입니다',
        ]
        
        for pattern in general_patterns:
            match = re.search(pattern, text)
            if match:
                results.append(match.group().strip())
                break
    
    # 복용/사용 시기 패턴
    timing_patterns = [
        r'식전|식후|식간',
        r'아침|점심|저녁|취침전',
        r'환부|상처부위',
        r'수회|여러\s*차례',
        r'점안|도포|바르|붙'
    ]
    
    timing = []
    for pattern in timing_patterns:
        matches = re.findall(pattern, text)
        timing.extend(matches)
    
    if timing:
        unique_timing = list(dict.fromkeys(timing))[:3]
        results.append(f"{'/'.join(unique_timing)}")

    # 용량 제한 패턴
    limit_patterns = [
        r'(\d+[매정포ml]\s*이상.*?사용하지)',
        r'(\d+일\s*이상.*?사용하지)',
        r'최대.*?(\d+[가-힣]*)',
    ]

    for pattern in limit_patterns:
        match = re.search(pattern, text)
        if match:
            results.append(f"제한: {match.group(1)}")
            break
    
    if results:
        return "; ".join(results)
    else:
        # 패턴 매칭 실패시 핵심 정보만
        # 숫자+단위 패턴 (매, 정, 포, mg, ml 등)
        dosage_numbers = re.findall(r'\d+[가-힣]*\s*\d+회|\d+일\s*\d+[매정포ml]|1회\s*\d+[가-힣]*|\d+[매정포캡슐방울mgml]', text)
        if dosage_numbers:
            return "; ".join(dosage_numbers[:3])
        return text[:50]
    
def extract_core_warnings(text: str) -> str:
    """주의사항에서 핵심 금기/주의 패턴만 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    # 금기 대상 패턴 (더 정확한 매칭)
    contraindication_patterns = [
        r'\d+세\s*미만.*?유아',
        r'\d+개월\s*이하.*?유아',
        r'임부|임신.*?여성',
        r'수유부',
        r'과민증\s*환자',
        r'피부\s*감염증',
        r'고막\s*천공',
        r'궤양.*?환자',
        r'화상.*?환자',
        r'고령자',
        r'[가-힣]*장애.*?환자',  # 신장장애, 간장애 등 추가
        r'[가-힣]*혈증.*?환자',  # 고마그네슘혈증 등 추가
    ]
    
    # 사용 제한 패턴
    restriction_patterns = [
        r'안과용.*?사용하지',
        r'외용.*?사용',
        r'장기간.*?사용하지',
        r'\d+일\s*이내.*?제한',
        r'치료.*?목적.*?사용하지',
        r'의사.*?감독.*?없이.*?사용하지',
    ]
    
    found_warnings = []
    
    # 금기 대상 추출
    for pattern in contraindication_patterns:
        matches = re.findall(pattern, text)
        if matches:
            found_warnings.extend(matches[:2])  # 최대 2개
    
    # 사용 제한 추출
    for pattern in restriction_patterns:
        matches = re.findall(pattern, text)
        if matches:
            found_warnings.extend(matches[:2])  # 최대 2개

    # 핵심 질환명 추출 (괄호 안 내용)
    disease_pattern = r'\(([^)]{3,15})\)'  # 3-15글자 괄호 내용
    diseases = re.findall(disease_pattern, text)
    if diseases:
        # 주요 질환명만 선별 (너무 많으면 3개까지)
        major_diseases = [d for d in diseases if len(d) <= 8][:3]
        if major_diseases:
            found_warnings.append(f"금기질환: {', '.join(major_diseases)}")
    
    if found_warnings:
        unique_warnings = list(dict.fromkeys(found_warnings))[:4]
        return "; ".join(unique_warnings)
    else:
        # 패턴 매칭 실패시 첫 문장의 핵심만
        # "마십시오" 앞까지만 추출
        match = re.search(r'^(.*?상의하십시오)', text)
        if match:
            return match.group(1)[:80]
        
        # 2순위: "마십시오" 앞까지만 추출
        match = re.search(r'^(.*?마십시오)', text)
        if match:
            return match.group(1)[:80]
        
        sentences = re.split(r'[.!]', text)
        if sentences:
            return sentences[0].strip()[:60]
        return text[:60]
    
def extract_core_interactions(text: str) -> str:
    """상호작용에서 약물명과 주의사항 패턴 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    # 약물 분류/계열 패턴 (우선순위)
    drug_class_patterns = [
        r'에스트로겐.*?피임약',
        r'비타민\s*[A-Z]',
        r'항응고제',
        r'당뇨병제',
        r'비만치료제',
        r'사하제',
        r'철분제',
        r'제산제',
        r'지질.*?약물',
        r'피임약',
        r'항생제',
    ]
    
    # 일반적인 약물명 패턴 (한글 + 영문)
    general_drug_patterns = [
        r'[가-힣]{3,8}(?:정|캡슐|액|크림|연고)',  # 한글약물명+제형
        r'[A-Za-z]{4,12}',  # 영문 약물명 (4-12글자)
        r'[가-힣]{2,6}(?:아미드|마이신|콜)',  # ~아미드, ~마이신 계열
    ]
    
    # 괄호 안 설명 패턴 (부가 정보)
    description_pattern = r'\(([^)]{3,15})\)'
    
    found_drugs = []
    # 1순위: 약물 분류 추출
    for pattern in drug_class_patterns:
        matches = re.findall(pattern, text)
        found_drugs.extend(matches)
    
    # 2순위: 일반 약물명 패턴 (분류가 부족할 때만)
    if len(found_drugs) < 3:
        for pattern in general_drug_patterns:
            matches = re.findall(pattern, text)
            # 너무 일반적인 단어 제외
            filtered_matches = [m for m in matches if m not in ['사용', '복용', '함께', '경구', '포함']]
            found_drugs.extend(filtered_matches)

    # 3순위: 괄호 안 중요 정보
    descriptions = re.findall(description_pattern, text)
    important_descriptions = [d for d in descriptions if any(keyword in d for keyword in ['용', '제', '약', '성'])]
    found_drugs.extend(important_descriptions[:2])
    
    # 상호작용 지시사항 확인
    if '함께' in text and ('마십시오' in text or '상의' in text):
        action_suffix = "병용주의"
    else:
        action_suffix = "상호작용"
    
    if found_drugs:
        unique_drugs = list(dict.fromkeys(found_drugs))[:4]  # 최대 4개
        return f"{', '.join(unique_drugs)} {action_suffix}"
    else:
        # 모든 패턴 실패시
        if '함께' in text:
            return "다수 약물과 병용주의"
        return text[:40]
    
def extract_core_side_effects(text: str) -> str:
    """부작용에서 증상 패턴만 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    # 부작용 증상 패턴
    symptom_patterns = [
        r'[가-힣]{2,}감',         # ~감 (열감, 소양감 등)
        r'[가-힣]{2,}증',         # ~증 (가려움증 등)
        r'발진|가려움|부종|충혈',     # 피부 증상
        r'구역|구토|설사|변비',       # 소화기 증상  
        r'졸음|어지러움|두통|피로',   # 신경계 증상
        r'심계항진|호흡곤란',        # 순환기 증상
        r'작열감|자극감|따끔',       # 자극 증상
    ]
    
    found_symptoms = []
    for pattern in symptom_patterns:
        matches = re.findall(pattern, text)
        found_symptoms.extend(matches)
    
    if found_symptoms:
        # 중복 제거 로직 개선
        unique_symptoms = []
        seen = set()
        for symptom in found_symptoms:
            # "가려움"과 "가려움증" 중복 처리
            normalized = symptom.replace('증', '').replace('감', '')
            if normalized not in seen:
                seen.add(normalized)
                unique_symptoms.append(symptom)
        
        return ", ".join(unique_symptoms[:6])
    else:
        # 패턴 매칭 실패시 핵심 부분만
        cleaned = re.sub(r'드물게\s*', '', text)
        cleaned = re.sub(r'나타나는\s*경우.*', '', cleaned)
        cleaned = re.sub(r'복용을\s*즉각\s*중지.*', '', cleaned)
        return cleaned.strip()[:50]

def extract_core_storage(text: str) -> str:
    """보관법에서 보관 조건 패턴만 추출"""
    if not text or len(text.strip()) < 5:
        return ""
    
    # 보관 조건 패턴
    storage_patterns = [
        r'실온.*?보관',
        r'냉장.*?보관', 
        r'습기.*?피해',
        r'빛.*?피해',
        r'직사광선.*?피해',
        r'어린이.*?손.*?닿지.*?않는.*?곳',
        r'\d+도.*?보관',
    ]
    
    storage_conditions = []
    for pattern in storage_patterns:
        matches = re.findall(pattern, text)
        storage_conditions.extend(matches)
    
    if storage_conditions:
        unique_conditions = list(dict.fromkeys(storage_conditions))[:3]
        return "; ".join(unique_conditions)
    else:
        return text[:40]
    
# 통합 핵심 추출 함수
def extract_all_core_info(document: Dict) -> Dict:
    """문서의 모든 필드에서 정규식 패턴으로 핵심 정보 추출"""
    core_document = document.copy()
    
    # 각 필드별 정규식 추출 적용
    field_extractors = {
        '효과': extract_core_effects,
        '복용법': extract_core_dosage, 
        '주의사항': extract_core_warnings,
        '상호작용': extract_core_interactions,
        '부작용': extract_core_side_effects,
        '보관법': extract_core_storage
    }
    
    for field, extractor in field_extractors.items():
        if field in core_document and core_document[field]:
            original = core_document[field]
            extracted = extractor(original)
            if extracted:
                core_document[field] = extracted
    
    return core_document

# 임베딩용 텍스트 생성 함수 
def create_embedding_content(document: Dict) -> str:
    """문서에서 임베딩용 텍스트 동적 생성"""
    product_name = document['product_name']
    content_parts = [f"약물: {product_name}"]

    # 성분명 추출 (괄호 안의 내용)
    if '(' in product_name and ')' in product_name:
        ingredient = product_name.split('(')[1].split(')')[0]
        content_parts.append(f"성분: {ingredient}")

    # 약물 정보 필드들 추가 (순서 중요)
    info_fields = [
        '효과',
        '복용법', 
        '주의사항',
        '상호작용',
        '부작용',
        '보관법'
    ]

    for field in info_fields:
        if field in document and document[field]:
            content_parts.append(f"{field}: {document[field]}")
    
    return "\n".join(content_parts)

def item_to_documents(item: Dict, search_drug: str = None) -> List[Dict]:
    """API 응답 아이템을 문서로 변환"""

    product_name = item.get('itemName', '').strip()
    company_name = item.get('entpName', '').strip()

    if not product_name:
        return []
    
    # 성분명 추출 (URL용)
    ingredient_name = ""
    if '(' in product_name and ')' in product_name:
        ingredient_name = product_name.split('(')[1].split(')')[0]
    
    # URL 생성 - 성분명 우선, 없으면 제품명
    search_keyword = ingredient_name if ingredient_name else product_name
    drug_url = f"https://nedrug.mfds.go.kr/search?keyword={urllib.parse.quote(search_keyword)}"

    # 기본 문서 구조
    document = {
        "drug_name": search_drug or product_name,
        "product_name": product_name,
        "company_name": company_name,
        "source": f"식약처 의약품개요정보 - {product_name}",
        "url": drug_url,
        "category": "통합약물정보"
    }
    
    # 직접 필드 매핑 (검색 키워드 풍부화)
    field_mapping = {
        'efcyQesitm': '효과',
        'useMethodQesitm': '복용법',
        'atpnQesitm': '주의사항',
        'intrcQesitm': '상호작용',
        'seQesitm': '부작용',
        'depositMethodQesitm': '보관법'
    }

    # 각 필드 정보를 직접 문서에 추가
    added_fields = 0

    for api_field, doc_field in field_mapping.items():
        content = item.get(api_field, '')

        if is_valid_content(content):
            cleaned_content = clean_text(content)

            if len(cleaned_content) > 15:
                document[doc_field] = cleaned_content
                added_fields += 1

    # 유효한 정보가 없으면 빈 리스트 반환
    if added_fields == 0:
        return []
    
    # 🆕 정규식 패턴으로 핵심 추출
    core_document = extract_all_core_info(document)
    return [core_document]
