# app/simple_test.py
import os
from dotenv import load_dotenv

load_dotenv()

print("🧪 환경 설정 테스트")
print("=" * 30)

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ API 키 발견: {api_key[:10]}...")
    if api_key.startswith("sk-"):
        print("✅ API 키 형식이 올바릅니다")
    else:
        print("❌ API 키 형식이 잘못되었습니다 (sk-로 시작해야 함)")
else:
    print("❌ API 키가 설정되지 않았습니다")

print("🎉 기본 설정 테스트 완료!")