# AI 광고 크리에이터

**AI 기반 완전 자동 광고 영상 생성 시스템**

브랜드명과 키워드만 입력하면 AI가 자동으로 **컨셉 기획 → 이미지 생성 → 음성 생성 → 영상 합성**까지 모든 과정을 처리하여 완성된 30초 광고 영상을 생성합니다.

<img width="921" height="897" alt="image" src="https://github.com/user-attachments/assets/ae2f2dc3-6208-4f8d-8b69-0e18299eecb6" />



## 주요 기능

### 완전 자동 광고 생성
- **브랜드 + 키워드** 입력만으로 완성된 광고 영상 생성
- **GPT-4o** 기반 창의적 광고 컨셉 생성
- **DALL-E 3** 고품질 이미지 생성
- **OpenAI TTS** 자연스러운 음성 나레이션
- **CogVideoX-2b** AI 비디오 생성
- **Riffusion** 배경음악 생성

### 품질 검증 시스템
- **Whisper** 기반 음성 품질 자동 검증
- **실시간 품질 점수** 측정 및 재생성
- **텍스트 유사도 검증**으로 정확한 나레이션 보장

### 브랜드 맞춤 최적화
- **브랜드별 프롬프트 최적화** (나이키, 스타벅스, 애플, 삼성 등)
- **스타일 기반 영상 생성** (모던, 미니멀, 역동적 등)
- **타겟 고객층 맞춤** 컨텐츠 생성

### 사용자 친화적 인터페이스
- **웹 기반 GUI** - 직관적인 사용자 인터페이스
- **실시간 진행 상황** 모니터링
- **원클릭 다운로드** 기능

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/DataScientist-CL/ai-ad-creator.git
cd ai-ad-creator

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# HuggingFace 토큰 (CogVideoX 사용 시)
HF_TOKEN=hf_your-huggingface-token-here

# 프로젝트 설정
PROJECT_ROOT=./
ENABLE_QUALITY_VALIDATION=true
WHISPER_MODEL=base
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

### 3. 시스템 요구사항 확인

```bash
# FFmpeg 설치 확인
ffmpeg -version

# GPU 확인 (선택사항)
nvidia-smi
```

**FFmpeg 설치 가이드:**
- **Windows**: `winget install --id=Gyan.FFmpeg -e`
- **macOS**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt update && sudo apt install ffmpeg`

### 4. 서버 실행

```bash
python main.py
```

<img width="617" height="203" alt="image" src="https://github.com/user-attachments/assets/da1b77ea-2e92-4c20-a88f-5423b39ead0e" />



서버가 실행되면 브라우저에서 `http://localhost:8000`으로 접속하세요.

## 사용 방법

### 웹 인터페이스 사용

1. **브라우저에서 접속**: `http://localhost:8000`
2. **브랜드명 입력**: 예) "스타벅스", "나이키", "애플"
3. **키워드 입력**: 예) "겨울 신메뉴, 따뜻한 커피, 아늑한 분위기"
4. **설정 선택**: 영상 길이, 품질, 음성 등
5. **생성 시작**: 진행 상황을 실시간으로 확인

![462383753-0fdd8b05-ad35-42ad-ac28-675b09ef30da](https://github.com/user-attachments/assets/d5daa4c7-9d29-4e7e-9601-b309a14455dd)



6. **다운로드**: 완성된 영상을 다운로드
<img width="578" height="328" alt="image" src="https://github.com/user-attachments/assets/22cbf4da-be2c-4ce2-b0e8-9338daa0d016" />


### API 직접 사용

```python
import requests

# 광고 생성 요청
response = requests.post("http://localhost:8000/api/v1/ads/create-complete", 
    json={
        "brand": "스타벅스",
        "keywords": "겨울 신메뉴, 따뜻한 커피, 아늑한 분위기",
        "duration": 30,
        "voice": "nova"
    }
)

task_id = response.json()["task_id"]

# 진행 상황 확인
status_response = requests.get(f"http://localhost:8000/api/v1/ads/status/{task_id}")
print(status_response.json())
```

## 시스템 구조

```
ai-ad-creator/
├── main.py                 # FastAPI 서버 메인
├── app/
│   ├── agents/            # AI 에이전트들
│   │   ├── agents.py      # 컨셉, 이미지, 음성 에이전트
│   │   ├── workflow.py    # LangGraph 워크플로우
│   │   └── quality_validator.py  # 품질 검증 시스템
│   ├── core/              # 핵심 클라이언트
│   │   ├── openai_client.py
│   │   └── mock_openai_client.py
│   └── utils/             # 유틸리티
│       └── CogVideoX_2b_utils.py
├── generated/             # 생성된 콘텐츠
│   ├── audio/            # 음성 파일
│   ├── images/           # 이미지
│   ├── videos/           # 비디오
│   └── final/            # 최종 합성 영상
├── templates/            # 웹 UI
│   └── complete_ad_creator.html
├── tests/                # 테스트 스크립트
├── requirements.txt      # 의존성 패키지
└── .env                 # 환경 변수
```

## 지원 기능

### AI 모델
- **GPT-4o**: 광고 컨셉 생성
- **DALL-E 3**: 고품질 이미지 생성
- **OpenAI TTS**: 자연스러운 음성 합성
- **CogVideoX-2b**: AI 비디오 생성
- **Whisper**: 음성 품질 검증
- **Riffusion**: 배경음악 생성

### 영상 품질 옵션
- **Fast**: 빠른 생성 (~1분)
- **Balanced**: 균형 잡힌 품질 (~3분)
- **High**: 고품질 생성 (~5분)

### 음성 옵션
- **6가지 음성**: Alloy, Echo, Fable, Onyx, Nova, Shimmer
- **다국어 지원**: 한국어, 영어 등

## 테스트 및 디버깅

### 시스템 상태 확인
```bash
# 헬스체크
curl http://localhost:8000/health

# 품질 검증 테스트
python quick_test.py

# 완전 통합 테스트
python complete_ad_test.py
```

### 오프라인 시각화
```bash
# 서버 없이 결과 시각화
python offline_visualizer.py

# 기존 작업 결과 시각화
python visualize_ad.py
```

## 고급 설정

### GPU 사용 (권장)
- **CUDA 12.1+** 설치
- **8GB+ VRAM** 권장 (RTX 3070 이상)
- GPU 메모리 최적화 자동 적용

### 환경 변수 상세 설정
```env
# 품질 검증 설정
ENABLE_QUALITY_VALIDATION=true
WHISPER_MODEL=base
MIN_QUALITY_SCORE=0.8
MAX_RETRY_ATTEMPTS=2

# 비디오 생성 설정
VIDEO_QUALITY=balanced
ENABLE_BGM=true
BGM_STYLE=auto

# 디버깅 설정
USE_MOCK_MODE=false
REAL_AI_MODE=true
```

## 성능 최적화

### 권장 시스템 사양
- **CPU**: Intel i7 또는 AMD Ryzen 7 이상
- **메모리**: 16GB RAM 이상
- **GPU**: NVIDIA RTX 4070 이상 (8GB VRAM)
- **저장공간**: SSD 50GB 이상

### 생성 시간 가이드
- **Fast 모드**: ~1분 (CPU 가능)
- **Balanced 모드**: ~3분 (GPU 권장)
- **High 모드**: ~5분 (GPU 필수)

## 문제 해결

### 일반적인 문제들

**1. OpenAI API 오류**
```bash
# API 키 확인
echo $OPENAI_API_KEY
```

**2. FFmpeg 누락**
```bash
# FFmpeg 설치 확인
ffmpeg -version
```

**3. GPU 메모리 부족**
```bash
# GPU 메모리 확인
nvidia-smi
```

**4. 품질 검증 실패**
```bash
# Whisper 모델 확인
python -c "import whisper; print(whisper.available_models())"
```

### 로그 확인
```bash
# 서버 로그
python main.py

# 상세 디버깅
python main.py --debug
```

## 프로젝트 회고

### 성공적으로 구현된 기능들

**OpenAI TTS 음성 생성**
- 자연스러운 한국어 음성 합성 완벽 구현
- 6가지 음성 옵션으로 다양한 브랜드 톤앤매너 지원
- 실시간 음성 품질 검증 시스템 안정적 작동

**Whisper 품질 검증 시스템**
- STT 기반 음성-텍스트 일치도 검증 성공
- 자동 재생성 로직으로 품질 기준 미달 시 개선
- 텍스트 유사도 분석으로 정확한 나레이션 보장

**DALL-E 3 이미지 생성**
- 브랜드별 맞춤형 이미지 생성 최적화
- 고품질 1024x1024 해상도 이미지 안정적 생성
- 스타일 기반 이미지 생성으로 브랜드 일관성 유지

### 개선이 필요한 영역들

**Text-to-Video 모델 한계**
- **CogVideoX-2b 모델의 제약사항**: 생성되는 영상이 5초 내외로 짧음
- **해결 방안**: 더 긴 영상 생성이 가능한 모델로 업그레이드 필요
  - Runway Gen-2/3, Pika Labs, Stable Video Diffusion 등 검토
  - 영상 길이 확장을 위한 세그먼트 기반 생성 로직 개발

**BGM 생성 모델 개선 필요**
- **Riffusion 모델의 한계**: 광고 컨셉과 완전히 일치하는 BGM 생성 어려움
- **개선 방향**: 
  - 브랜드/업종별 BGM 스타일 데이터셋 구축
  - MusicGen, AudioCraft 등 대안 모델 검토
  - 컨셉-음악 매칭 정확도 향상을 위한 추가 훈련 필요

### 향후 개발 방향


- CogVideoX 대안 모델 연구 및 적용
- 브랜드 가이드라인 자동 반영 시스템
- BGM 생성 품질 개선 및 스타일 다양화
- - 영상 길이 확장을 위한 세그먼트 연결 로직 최적화
  

### 학습 성과

이 프로젝트를 통해 **멀티모달 AI 시스템 구축**의 복잡성과 각 모델의 특성을 깊이 이해할 수 있었습니다. 특히 **실제 상용 서비스 수준의 품질 보장**을 위해서는 단순한 모델 조합 이상의 세밀한 최적화와 검증 시스템이 필요함을 체험했습니다.


---



## 감사의 말

- **OpenAI**: GPT-4o, DALL-E 3, TTS, Whisper
- **HuggingFace**: CogVideoX-2b, Diffusers
- **Meta**: MusicGen
- **Riffusion**: AI 음악 생성
- **FastAPI**: 웹 프레임워크
- **FFmpeg**: 비디오 처리



## 라이센스

이 프로젝트는 MIT 라이센스 하에 제공됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요. 



## 지원

- **Issues**: [GitHub Issues](https://github.com/DataScientist-CL/ai-ad-creator/issues)
- **Documentation**: [Wiki](https://github.com/DataScientist-CL/ai-ad-creator/wiki)
- **API 문서**: `http://localhost:8000/docs`
