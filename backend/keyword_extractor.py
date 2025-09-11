import json
from typing import List, Tuple
class OpenAIKeywordExtractor:
    def __init__(self, openai_client):
        self.client = openai_client
        

    def extract_search_keywords(self, query: str) -> Tuple[List[str], List[str]]:
        """OpenAI를 사용해 자연어에서 약물명과 증상 키워드 추출"""

        function_schema = {
            "name": "extract_medical_keywords",
            "description": "사용자 질문에서 약물명과 증상을 추출합니다",
            "parameters": {
                "type" : "object",
                "properties": {
                    "drug_names" : {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추출된 약물명들 (상품명, 성분명 포함)"
                    },
                    "symptoms": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "추출된 증상들 (의학 용어로 정규화)"
                    },
                    "search_intent": {
                        "type": "string",
                        "enum": ["drug_info", "symptom_treatment", "drug_interaction", "general"],
                        "description": "검색 의도 분류"
                    }
                },
                 "required": ["drug_names", "symptoms", "search_intent"]
            }
        }

        messages = [
                {
                    "role": "system",
                    "content": """너는 약학정보 검색을 위한 키워드 추출 전문가야. 
사용자의 질문을 분석하여:
1. 약물명 추출 (사용자가 언급한 약물명만, 성분명으로 확장하지 말 것)
2. 증상을 의학용어로 정규화 (예: "머리 아파" -> "두통")
3. 검색 의도 분류

예시:
- "타이레놈 먹어도 되나요?" → drug_names: ["타이레놀"], symptoms: [], intent: "drug_info"   
- "임신 중 머리가 아픈데 뭘 먹어야 할까요?" → drug_names: [], symptoms: ["임신", "두통"], intent: "symptom_treatment"
- "감기약과 두통약 같이 먹어도 돼?" → drug_names: [], symptoms: ["감기", "두통"], intent: "drug_interaction"
"""
            },
            {"role": "user", "content": f"다음 질문을 분석해주세요: {query}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=[function_schema],
                function_call={"name": "extract_medical_keywords"},
                temperature=0.1,
                max_tokens=300
            )

            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "extract_medical_keywords":
                result = json.loads(function_call.arguments)

                drug_names = result.get("drug_names", [])
                symptoms = result.get("symptoms", [])
                intent = result.get("search_intent", "general")
                
                return drug_names, symptoms, intent
            
        except Exception as e:
            print(f"❌ AI 키워드 추출 실패: {e}")
            
        # 실패시 폴백
        return [], [], "general"

        
        



