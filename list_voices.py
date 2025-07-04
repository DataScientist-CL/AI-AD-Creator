# list_voices.py
from elevenlabs.client import ElevenLabs

# 1) 환경변수 대신 직접 키를 하드코딩
client = ElevenLabs(api_key="sk_7f5157e3203ee6318d3678898ac7a01f046c695752e636b3")

# 2) ElevenLabs v2 SDK에서 제공하는 메서드로 목소리 목록 가져오기
response = client.voices.search()
voices = response.voices

# 3) 출력
print("Available voices:")
for v in voices:
    print(f"  • {v.voice_id} — {v.name}")


