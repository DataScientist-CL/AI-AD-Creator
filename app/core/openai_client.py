# app/core/openai_client.py
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class OpenAIClient:
    """OpenAI API 클라이언트"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다!")
        
        self.client = OpenAI(api_key=self.api_key)
        print("✅ OpenAI 클라이언트 초기화 완료")
    
    def generate_concept(self, brand: str, keywords: str) -> str:
        """광고 컨셉 생성"""
        # 영어로 프롬프트 작성
        prompt = f"""Create a 30-second advertisement concept for {brand}.
        
Keywords: {keywords}

Please provide in Korean:
1. Main marketing message
2. Three scenes with descriptions
3. Narration script
4. Visual style recommendations

Make it creative and engaging for Korean audience."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative advertising expert. Always respond in Korean."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            concept = response.choices[0].message.content
            print("✅ 광고 컨셉 생성 완료")
            return concept
            
        except Exception as e:
            print(f"❌ 컨셉 생성 실패: {str(e)}")
            raise
    
    def generate_image_prompt(self, scene_description: str) -> str:
        """DALL-E 이미지 생성 프롬프트 생성"""
        prompt = f"""Create a detailed DALL-E prompt for: {scene_description}

Requirements:
- Professional commercial photography style
- High quality, cinematic lighting
- Brand-appropriate atmosphere
- Realistic, not cartoonish
- Warm and inviting mood"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional photographer and visual director."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            image_prompt = response.choices[0].message.content
            print("✅ 이미지 프롬프트 생성 완료")
            return image_prompt
            
        except Exception as e:
            print(f"❌ 이미지 프롬프트 생성 실패: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say hello in Korean"}],
                max_tokens=50
            )
            print(f"🔗 API 연결 테스트: {response.choices[0].message.content}")
            return True
        except Exception as e:
            print(f"❌ API 연결 실패: {str(e)}")
            return False

def test_full_workflow():
    """전체 워크플로우 테스트"""
    print("🧪 AI 광고 생성 시스템 테스트 시작!\n")
    
    try:
        # 클라이언트 초기화
        client = OpenAIClient()
        
        # 1. API 연결 테스트
        print("1️⃣ API 연결 테스트")
        if not client.test_connection():
            return False
        
        # 2. 광고 컨셉 생성
        print("\n2️⃣ 광고 컨셉 생성")
        concept = client.generate_concept("Starbucks", "winter menu, cozy atmosphere, holiday season")
        print(f"\n📋 생성된 광고 컨셉:\n{concept}\n")
        
        # 3. 이미지 프롬프트 생성
        print("3️⃣ 이미지 프롬프트 생성")
        image_prompt = client.generate_image_prompt("cozy Starbucks cafe with winter decorations and people enjoying hot drinks")
        print(f"\n🖼️ DALL-E 프롬프트:\n{image_prompt}\n")
        
        print("🎉 모든 테스트 성공! AI 광고 생성 시스템이 준비되었습니다!")
        return True
        
    except Exception as e:
        print(f"💥 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    test_full_workflow()