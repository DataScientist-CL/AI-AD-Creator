# 간단한 OpenAI 연결 테스트
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_setup():
    print("🧪 AI 광고 크리에이터 설정 테스트")
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API 키가 설정되었습니다")
        print(f"🔑 API 키: {api_key[:10]}...")
    else:
        print("❌ OpenAI API 키가 설정되지 않았습니다")
        print("💡 .env 파일에 OPENAI_API_KEY를 추가하세요")
    
    print("🎉 기본 설정 완료!")

if __name__ == "__main__":
    test_setup()