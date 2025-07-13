# main.py — AI 광고 크리에이터 FastAPI 서버 (CogVideoX + TTS + BGM 통합) - 30초 완성 버전 (개선)

# ─────────────────────────────────────────────
# 1) 환경 변수 로드 및 초기 설정, 필수 라이브러리 임포트
# ─────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv() # .env 파일에서 환경 변수 로드

# --- API KEY 존재 여부 즉시 확인 - 디버깅 코드 ---
import os
_debug_api_key = os.getenv("OPENAI_API_KEY")
if _debug_api_key:
    print(f"✅ DEBUG: OpenAI API Key가 환경 변수에서 성공적으로 로드되었습니다!")
    print(f"DEBUG: 키 시작 부분: {_debug_api_key[:5]}...")
else:
    print(f"❌ DEBUG: OpenAI API Key가 환경 변수에서 로드되지 않았습니다.")
# --- 디버깅 코드 끝 ---

# 1) 표준 라이브러리 임포트 (Python 기본 제공 모듈)
import sys # 시스템 관련 파라미터 및 함수에 접근하기 위한 모듈입니다.
import uuid # 고유 식별자(UUID) 생성을 위한 모듈입니다 (예: 작업 ID).
import asyncio # 비동기 프로그래밍을 위한 모듈입니다.
import subprocess # 외부 프로세스(예: FFmpeg)를 실행하고 관리하기 위한 모듈입니다.
import json # JSON 데이터 처리(인코딩/디코딩)를 위한 모듈입니다.
import math # 수학 함수를 위한 모듈입니다.

from pathlib import Path # 파일 시스템 경로를 객체 지향적으로 다루기 위한 모듈입니다.
from datetime import datetime # 날짜 및 시간 객체를 다루기 위한 모듈입니다.
from typing import Dict, Any, Optional, List, Literal # 타입 힌트(Type Hinting)를 위한 모듈입니다.

# 2) 서드파티 라이브러리 임포트 (pip으로 설치하는 외부 모듈)
from pydantic import BaseModel, Field # FastAPI에서 데이터 유효성 검사 및 설정 관리를 위한 모델 정의에 사용됩니다.
                                      # FastAPI 요청 모델 정의보다 먼저 임포트되어야 합니다.

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request # FastAPI 프레임워크의 핵심 구성 요소입니다.
                                                                     # FastAPI: 웹 애플리케이션 생성, HTTPException: HTTP 오류 응답,
                                                                     # BackgroundTasks: 백그라운드 작업 실행, Request: HTTP 요청 객체.
from fastapi.middleware.cors import CORSMiddleware # CORS(Cross-Origin Resource Sharing) 정책을 설정하는 미들웨어입니다.
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse # FastAPI 응답 유형입니다.
                                                                        # JSONResponse: JSON 데이터 응답, HTMLResponse: HTML 페이지 응답,
                                                                        # FileResponse: 파일 다운로드 응답.
from fastapi.templating import Jinja2Templates # Jinja2 템플릿 엔진을 사용하여 HTML 템플릿을 렌더링합니다.

# 3) 로컬 애플리케이션 모듈 임포트

# CogVideoX 유틸리티 로드 (새로운 방식)
try:
    from app.utils.cogvideo_utils import CogVideoXGenerator, check_cogvideo_installation # CogVideoX 비디오 생성 관련 유틸리티를 임포트합니다.
    COGVIDEO_AVAILABLE = True # CogVideoX 모듈이 성공적으로 로드되었음을 나타내는 플래그입니다.
    print("✅ CogVideoX utils 모듈 로드 성공")
except ImportError as e:
    COGVIDEO_AVAILABLE = False # 로드 실패 시 플래그를 False로 설정합니다.
    print(f"⚠️ CogVideoX utils 모듈 로드 실패: {e}")

# 기존 CogVideoX 모듈 로드 시도 (하위 호환성)
try:
    from app.utils.video_utils import generate_with_cogvideo # 이전 버전의 CogVideoX 유틸리티를 임포트합니다 (폴백용).
    COGVIDEO_LEGACY_AVAILABLE = True # 레거시 CogVideoX 모듈이 성공적으로 로드되었음을 나타내는 플래그입니다.
    print("✅ Legacy CogVideoX utils 모듈 로드 성공")
except ImportError as e:
    COGVIDEO_LEGACY_AVAILABLE = False # 로드 실패 시 플래그를 False로 설정합니다.
    print(f"⚠️ Legacy CogVideoX utils 모듈 로드 실패: {e}")
    print("📌 CogVideoX 기능 없이 기본 이미지+오디오 합성 모드로 실행됩니다.")

# Riffusion BGM 로드
try:
    from app.utils.riffusion_utils import BGMGenerator, generate_multiple_bgm_styles, check_riffusion_installation # Riffusion BGM 생성 유틸리티를 임포트합니다.
    RIFFUSION_AVAILABLE = True # Riffusion 모듈이 성공적으로 로드되었음을 나타내는 플래그입니다.
    print("✅ Riffusion BGM 모듈 로드 성공")
except ImportError as e:
    RIFFUSION_AVAILABLE = False # 로드 실패 시 플래그를 False로 설정합니다.
    print(f"⚠️ Riffusion BGM 모듈 로드 실패: {e}")

# ─────────────────────────────────────────────
# 2) FastAPI 애플리케이션 초기화
# ─────────────────────────────────────────────
app = FastAPI( # FastAPI 애플리케이션 인스턴스를 생성합니다.
    title="🎬 AI Complete Advertisement Creator API", # API 문서(Swagger UI/ReDoc)에 표시될 제목입니다.
    description="AI 기반 멀티모달 광고 콘텐츠 생성 및 품질 검증 시스템 (CogVideoX + TTS + BGM)", # API 문서에 표시될 설명입니다.
    version="3.1.0", # API 버전입니다.
    docs_url="/docs", # Swagger UI 문서의 URL 경로입니다.
    redoc_url="/redoc", # ReDoc 문서의 URL 경로입니다.

    swagger_ui_favicon_url="/favicon.ico", # Swagger UI에 표시될 파비콘 경로입니다.
    redoc_favicon_url="/favicon.ico" # ReDoc에 표시될 파비콘 경로입니다.
)

# Jinja2 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates") # "templates" 폴더에서 HTML 템플릿을 찾도록 Jinja2를 설정합니다.

# CORS (Cross-Origin Resource Sharing) 설정
app.add_middleware( # FastAPI 애플리케이션에 미들웨어를 추가합니다.
    CORSMiddleware, # CORS 미들웨어입니다.
    allow_origins=["*"], # 모든 출처(origin)에서의 요청을 허용합니다 (개발 환경에서 편리, 프로덕션에서는 특정 도메인으로 제한 권장).
    allow_credentials=True, # 자격 증명(쿠키, HTTP 인증 등)을 함께 보낼 수 있도록 허용합니다.
    allow_methods=["*"], # 모든 HTTP 메소드(GET, POST, PUT 등)를 허용합니다.
    allow_headers=["*"], # 모든 HTTP 헤더를 허용합니다.
)

# ─────────────────────────────────────────────
# 3) 전역 상태 및 지연 초기화 워크플로우 정의
# ─────────────────────────────────────────────
# 비동기 작업을 저장하고 상태를 추적하는 딕셔너리
tasks_storage: Dict[str, Dict[str, Any]] = {} # 각 비동기 작업의 상태와 결과를 저장하는 전역 딕셔너리입니다.

# 프로젝트 루트 경로를 시스템 경로에 추가하여 모듈 임포트를 용이하게 합니다.
project_root = Path(__file__).parent # 현재 파일의 상위 디렉토리(프로젝트 루트) 경로를 가져옵니다.
sys.path.append(str(project_root)) # 이 경로를 Python 모듈 검색 경로에 추가하여 하위 모듈을 쉽게 임포트할 수 있도록 합니다.

# AI 워크플로우는 첫 요청 시에 초기화됩니다. (지연 초기화)
ai_workflow = None # AI 광고 생성 워크플로우 객체입니다. 초기에는 None으로 설정하여 지연 초기화를 수행합니다.
WORKFLOW_AVAILABLE = False # AI 워크플로우의 가용성 상태를 나타내는 플래그입니다.

def initialize_workflow():
    """AI 워크플로우 (AdCreatorWorkflow)를 지연 초기화하는 함수"""
    global ai_workflow, WORKFLOW_AVAILABLE # 전역 변수에 접근하기 위해 global 키워드를 사용합니다.
    if ai_workflow is None: # 워크플로우가 아직 초기화되지 않았다면
        try:
            print("🔄 AI 워크플로우 지연 초기화 시작...")
            # AdCreatorWorkflow 클래스를 동적으로 임포트합니다.
            from app.agents.workflow import AdCreatorWorkflow # AdCreatorWorkflow 클래스를 임포트합니다.
            api_key = os.getenv("OPENAI_API_KEY") # OpenAI API 키를 환경 변수에서 가져옵니다.
            if api_key:
                print(f"✅ 워크플로우 초기화용 API Key 확인: {api_key[:5]}...")
                ai_workflow = AdCreatorWorkflow() # API 키가 있으면 AdCreatorWorkflow 객체를 생성합니다.
            else:
                print("❌ 워크플로우 초기화용 API Key를 찾을 수 없음")
                ai_workflow = AdCreatorWorkflow() # API 키가 없어도 워크플로우 객체 자체는 생성 (이후 단계에서 오류 발생 가능).
            WORKFLOW_AVAILABLE = True # 초기화 성공 시 플래그를 True로 설정합니다.
            print("✅ AI 워크플로우 초기화 완료")
        except ImportError as e: # 임포트 실패 시 (예: `app.agents.workflow` 모듈이 없거나 오류 발생 시)
            print(f"⚠️ AI 워크플로우 import 실패: {e}")
            WORKFLOW_AVAILABLE = False # 플래그를 False로 설정합니다.
            ai_workflow = None # 워크플로우 객체를 None으로 유지합니다.

# ─────────────────────────────────────────────
# 🎯 개선된 프롬프트 템플릿 및 유틸리티 함수들
# ─────────────────────────────────────────────

# 🆕 [수정] 기존 광고 생성을 위한 개선된 프롬프트 템플릿
PROMPT_TEMPLATE = """
You are an expert ad copywriter specializing in short-form video advertisements. # 당신은 짧은 영상 광고 전문가입니다.
Generate a JSON-formatted advertisement with three scenes for {brand}. # {brand}에 대한 세 장면으로 구성된 JSON 형식의 광고를 생성하세요.
Use these keywords: {keywords}. # 다음 키워드를 사용하세요: {keywords}.
The campaign type is {campaign_type} and the style preference is {style_preference}. # 캠페인 유형은 {campaign_type}이며, 선호 스타일은 {style_preference}입니다.

IMPORTANT REQUIREMENTS: # 중요 요구사항:
1. First scene MUST show {brand} product clearly within first 3 seconds # 첫 번째 장면은 반드시 첫 3초 이내에 {brand} 제품을 명확히 보여야 합니다.
2. Each scene should be concise and product-focused # 각 장면은 간결하고 제품에 집중해야 합니다.
3. Visual descriptions must be clear and specific for AI video generation # AI 비디오 생성을 위해 시각적 설명은 명확하고 구체적이어야 합니다.
4. Include brand name and product in narration early # 나레이션 초기에 브랜드 이름과 제품을 포함하세요.
5. Focus on core product benefits and brand identity # 핵심 제품 이점과 브랜드 정체성에 집중하세요.

Return valid JSON in this exact format: # 다음 정확한 JSON 형식으로 반환하세요:
{
  "scenes": [
    {
      "name": "Scene name", # 장면 이름
      "duration": "time in seconds", # 장면 길이 (초 단위)
      "description": "visual description (in English, product-focused, specific)", # 시각적 설명 (영어, 제품 중심, 구체적)
      "narration": "voice-over text (Korean, brand name first)" # 보이스오버 텍스트 (한국어, 브랜드명 먼저)
    }
  ]
}

Brand-specific optimization examples: # 브랜드별 최적화 예시:
- Apple iPhone: "iPhone held in hands, premium metal design, iOS interface, Apple logo visible" # 애플 아이폰: "손에 들린 아이폰, 프리미엄 메탈 디자인, iOS 인터페이스, 애플 로고 보임"
- Nike shoes: "Nike running shoes closeup, athlete wearing them, swoosh logo prominent" # 나이키 신발: "나이키 러닝화 클로즈업, 선수가 착용, 스우시 로고 선명"
- Samsung Galaxy: "Samsung Galaxy phone displayed, advanced features demo, Samsung branding" # 삼성 갤럭시: "삼성 갤럭시 폰 전시, 고급 기능 시연, 삼성 브랜딩"
- Starbucks: "Starbucks coffee cup prominent, barista making drink, logo visible" # 스타벅스: "스타벅스 커피 컵 선명, 바리스타 음료 제조, 로고 보임"
"""

# 🆕 [새로 추가] 완전 통합 광고 생성을 위한 개선된 프롬프트 함수
def get_complete_ad_concept_prompt(brand, keywords, target_audience, style_preference, duration):
    """완전 통합 광고를 위한 개선된 컨셉 프롬프트 생성"""
    return f"""
당신은 전문 광고 제작자입니다. {duration}초 길이의 짧은 브랜드 광고를 제작해주세요.

브랜드: {brand}
키워드/컨셉: {keywords}
타겟: {target_audience}
스타일: {style_preference}
길이: {duration}초

--- 응답 형식 및 필수 지시 사항 ---
반드시 다음 JSON 형식으로 응답하며, 아래의 모든 지시사항을 철저히 따르세요:
{{
    "narration": "{brand} 브랜드명 포함한 {duration}초 길이의 상세하고 매력적인 나레이션. 나레이션 내용은 **반드시 한국어로만 작성하고**, {duration}초를 충분히 채울 수 있도록 길이를 조절해주세요.",
    "visual_description": "{brand} 제품이 첫 장면부터 명확히 나오는 구체적인 영어 영상 설명 (Visual description is for AI video generation, so it must be clear, specific, and in English. Ensure it captures the core concepts and brand identity, especially the product's early appearance.)"
}}

핵심 요구사항:
1. 나레이션은 **반드시 한국어로만** 작성하며, {brand} 브랜드명을 앞부분에 포함해야 합니다.
2. 나레이션은 요청된 {duration}초 길이를 완전히 채울 수 있도록 충분히 길고 상세하게 작성해야 합니다.
3. 영상 설명(visual_description)은 AI 비디오 생성용이므로, **반드시 구체적이고 명확한 영어로** 작성해야 합니다.
4. 첫 3초 안에 {brand} 제품/브랜드가 명확히 노출되도록 영상 설명을 구성해야 합니다.
5. {keywords}와 직접 연관된 핵심 기능/상황을 나레이션과 영상 설명에 모두 포함하세요.
6. 제품 중심의 간결하면서도 임팩트 있는 구성을 유지하되, 나레이션 길이를 충분히 확보하세요.

브랜드별 최적화 가이드:
- Apple iPhone: "iPhone in hands from first frame, premium design closeup, iOS interface interaction, Apple logo prominent"
- Nike shoes: "Nike running shoes closeup, athlete foot movement, swoosh logo visible, sports performance"
- Samsung Galaxy: "Samsung Galaxy phone center frame, advanced tech features demo, Samsung branding clear"
- Starbucks: "Starbucks coffee cup prominent first, steam rising, barista crafting, green logo visible"
- 코카콜라: "Coca-Cola bottle/can closeup first, refreshing pour, red logo prominent, classic branding"

스타일별 영상 톤 가이드:
- 모던하고 깔끔한: "modern clean minimalist professional"
- 따뜻하고 아늑한: "warm cozy comfortable lifestyle"
- 미니멀하고 프리미엄한: "premium luxury elegant sophisticated"
- 역동적이고 에너지: "dynamic energetic vibrant active"
- 감성적이고 로맨틱: "emotional romantic cinematic heartwarming"
- 전문적이고 신뢰: "professional corporate trustworthy business"
"""

# 🆕 [새로 추가] 향상된 CogVideoX 프롬프트 최적화 함수
def optimize_cogvideo_prompt_enhanced(brand, visual_description, keywords, style_preference):
    """🚀 개선된 CogVideoX 프롬프트 최적화 - 브랜드별 상세 시나리오 추가"""

    # 🎯 브랜드별 특화 비주얼 시나리오 사전 (대폭 개선)
    brand_scenarios = {
        "애플": {
            "visual_scenario": "Close-up of hands holding iPhone with elegant gestures, premium metal edges catching light, iOS interface animations, Apple logo subtly visible, minimalist white background with soft shadows",
            "product_focus": "iPhone premium design iOS interface Apple logo",
            "cinematography": "cinematic macro lens shallow depth of field"
        },
        "나이키": {
            "visual_scenario": "Dynamic athlete wearing Nike shoes in urban setting, sneaker closeup with swoosh logo, running motion with energy trails, sporty environment with modern architecture",
            "product_focus": "Nike shoes swoosh logo athletic performance",
            "cinematography": "dynamic camera movement high energy sports"
        },
        "삼성": {
            "visual_scenario": "Samsung Galaxy smartphone displaying advanced features, S Pen interaction, foldable screen technology, Samsung branding prominent, futuristic tech environment",
            "product_focus": "Samsung Galaxy smartphone S Pen technology branding",
            "cinematography": "high-tech modern commercial professional"
        },
        "스타벅스": {
            "visual_scenario": "Starbucks coffee cup with steam rising, skilled barista crafting latte art, cozy cafe atmosphere with warm lighting, green logo prominently displayed",
            "product_focus": "Starbucks coffee cup barista crafting green logo",
            "cinematography": "warm cozy atmosphere commercial lifestyle"
        },
        "코카콜라": {
            "visual_scenario": "Coca-Cola bottle/can with refreshing condensation, dynamic pour with bubbles, red branding prominent, classic American diner or summer setting",
            "product_focus": "Coca-Cola bottle refreshing pour red logo classic",
            "cinematography": "vibrant classic American commercial dynamic"
        },
        "엔디비아": {
            "visual_scenario": "NVIDIA RTX graphics card in high-end gaming setup, RGB lighting effects, multiple monitors displaying games/AI workloads, green LED accents, futuristic computer components",
            "product_focus": "NVIDIA RTX graphics card gaming setup RGB lighting green accents",
            "cinematography": "high-tech gaming futuristic professional commercial"
        }
    }

    # 🎨 스타일별 영상 톤 및 촬영 기법 사전 (개선)
    style_cinematography = {
        "모던하고 깔끔한": "modern clean minimalist professional lighting smooth camera movement",
        "따뜻하고 아늑한": "warm golden hour lighting cozy atmosphere soft focus comfortable",
        "미니멀하고 프리미엄한": "premium luxury elegant sophisticated clean lines high-end",
        "역동적이고 에너지": "dynamic energetic vibrant active fast-paced motion blur",
        "감성적이고 로맨틱": "emotional romantic cinematic heartwarming soft lighting",
        "전문적이고 신뢰": "professional corporate trustworthy business clean modern"
    }

    # 브랜드 특화 시나리오 가져오기
    brand_info = brand_scenarios.get(brand, {
        "visual_scenario": f"{brand} product showcase with professional presentation",
        "product_focus": f"{brand} product branding",
        "cinematography": "professional commercial"
    })

    # 스타일 촬영 기법 가져오기
    style_tech = style_cinematography.get(style_preference, "professional commercial")

    # 🎬 최종 최적화 프롬프트 생성 (구체적 시나리오 기반)
    optimized_prompt = f"""
{brand_info['visual_scenario']}, {visual_description}, 
{brand_info['product_focus']}, {style_tech}, 
{brand_info['cinematography']}, 
commercial advertisement, 4K resolution, high quality cinematography, 
product prominence from first frame, brand identity clear
""".strip().replace('\n', ' ').replace('  ', ' ')

    # 프롬프트 길이 최적화 (CogVideoX 효율성)
    if len(optimized_prompt) > 250:
        optimized_prompt = optimized_prompt[:250] + "..."
    
    return optimized_prompt

# 🆕 [새로 추가] 브랜드 필수 요소 검증 함수
def validate_brand_prompt(brand, prompt):
    """🔍 브랜드 필수 요소가 프롬프트에 포함되었는지 검증하고 보완"""
    
    # 브랜드별 필수 키워드 체크리스트
    brand_requirements = {
        "애플": ["iPhone", "Apple", "iOS"],
        "나이키": ["Nike", "shoes", "swoosh"],
        "삼성": ["Samsung", "Galaxy", "phone"],
        "스타벅스": ["Starbucks", "coffee", "logo"],
        "코카콜라": ["Coca-Cola", "bottle", "red"],
        "엔디비아": ["NVIDIA", "RTX", "graphics", "gaming"]
    }
    
    # 해당 브랜드의 필수 키워드가 있는지 확인
    if brand in brand_requirements:
        missing_keywords = []
        for keyword in brand_requirements[brand]:
            if keyword.lower() not in prompt.lower():
                missing_keywords.append(keyword)
        
        # 누락된 키워드가 있으면 보완
        if missing_keywords:
            prompt += f", {' '.join(missing_keywords)} prominent"
            print(f"🔧 브랜드 필수 요소 보완: {missing_keywords}")
    
    return prompt

# 🆕 [새로 추가] 향상된 음악적 BGM 생성 함수
def generate_enhanced_musical_bgm(duration: int, style_preference: str, output_dir: str):
    """🎵 향상된 음악적 BGM 생성 - 화음과 리듬 패턴 추가"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bgm_path = os.path.join(output_dir, f"enhanced_bgm_{style_preference}_{timestamp}.wav")
    
    # 🎼 스타일별 음악 이론 기반 설정
    musical_styles = {
        "모던하고 깔끔한": {
            "chord_progression": [
                {"root": 261.63, "third": 329.63, "fifth": 392.00},  # C major
                {"root": 220.00, "third": 277.18, "fifth": 329.63},  # A minor
                {"root": 196.00, "third": 246.94, "fifth": 293.66},  # G major
                {"root": 261.63, "third": 329.63, "fifth": 392.00}   # C major
            ],
            "rhythm_pattern": [1.0, 0.7, 0.5, 0.7] * (duration // 4),
            "effects": "aecho=0.6:0.8:500:0.15,highpass=f=120,lowpass=f=8000,chorus=0.5:0.9:50:0.4:0.25:2",
            "base_volume": 0.25
        },
        "따뜻하고 아늑한": {
            "chord_progression": [
                {"root": 220.00, "third": 277.18, "fifth": 329.63},  # A minor
                {"root": 196.00, "third": 246.94, "fifth": 293.66},  # G major  
                {"root": 261.63, "third": 329.63, "fifth": 392.00},  # C major
                {"root": 174.61, "third": 220.00, "fifth": 261.63}   # F major
            ],
            "rhythm_pattern": [1.0, 0.8, 0.6, 0.8] * (duration // 4),
            "effects": "aecho=0.8:0.9:800:0.25,highpass=f=80,lowpass=f=6000,chorus=0.6:0.8:60:0.5:0.3:2",
            "base_volume": 0.3
        },
        "미니멀하고 프리미엄한": {
            "chord_progression": [
                {"root": 130.81, "third": 164.81, "fifth": 196.00},  # C3 major
                {"root": 146.83, "third": 185.00, "fifth": 220.00},  # D major
                {"root": 164.81, "third": 207.65, "fifth": 246.94},  # E major
                {"root": 130.81, "third": 164.81, "fifth": 196.00}   # C3 major
            ],
            "rhythm_pattern": [1.0, 0.6, 0.4, 0.6] * (duration // 4),
            "effects": "aecho=0.5:0.7:400:0.1,highpass=f=150,lowpass=f=10000,reverb",
            "base_volume": 0.2
        },
        "역동적이고 에너지": {
            "chord_progression": [
                {"root": 146.83, "third": 185.00, "fifth": 220.00},  # D major
                {"root": 164.81, "third": 207.65, "fifth": 246.94},  # E major
                {"root": 196.00, "third": 246.94, "fifth": 293.66},  # G major
                {"root": 146.83, "third": 185.00, "fifth": 220.00}   # D major
            ],
            "rhythm_pattern": [1.0, 0.9, 0.8, 0.9] * (duration // 4),
            "effects": "aecho=0.4:0.6:300:0.2,highpass=f=90,lowpass=f=12000,chorus=0.4:0.7:40:0.3:0.2:3",
            "base_volume": 0.35
        },
        "감성적이고 로맨틱": {
            "chord_progression": [
                {"root": 174.61, "third": 220.00, "fifth": 261.63},  # F major
                {"root": 196.00, "third": 246.94, "fifth": 293.66},  # G major
                {"root": 220.00, "third": 277.18, "fifth": 329.63},  # A minor
                {"root": 174.61, "third": 220.00, "fifth": 261.63}   # F major
            ],
            "rhythm_pattern": [1.0, 0.7, 0.5, 0.7] * (duration // 4),
            "effects": "aecho=0.9:0.95:1000:0.3,highpass=f=70,lowpass=f=5000,chorus=0.7:0.9:80:0.6:0.4:2",
            "base_volume": 0.28
        }
    }
    
    # 기본 설정 (스타일별 설정이 없는 경우)
    style_config = musical_styles.get(style_preference, musical_styles["모던하고 깔끔한"])
    
    try:
        # 🎵 화음 기반 BGM 생성
        chord_progression = style_config["chord_progression"]
        rhythm_pattern = style_config["rhythm_pattern"][:duration]  # 길이에 맞게 조정
        
        # 각 화음별 사인파 생성
        chord_inputs = []
        volume_filters = []
        
        chord_duration = duration / len(chord_progression)
        
        for chord_idx, chord in enumerate(chord_progression):
            start_time = chord_idx * chord_duration
            
            # 화음의 각 음 (근음, 3음, 5음) 생성
            for note_idx, (note_name, frequency) in enumerate(chord.items()):
                input_name = f"chord{chord_idx}_{note_name}"
                volume_level = style_config["base_volume"] * (1.0 - note_idx * 0.1)  # 근음이 가장 크게
                
                chord_inputs.append(f"sine=frequency={frequency}:duration={chord_duration}")
                volume_filters.append(f"[{len(chord_inputs)-1}]volume={volume_level}[{input_name}]")
        
        # 🎼 리듬 패턴 적용 (볼륨 조절)
        rhythm_filters = []
        for i, vol_mult in enumerate(rhythm_pattern):
            if i < len(volume_filters):
                original_vol = float(volume_filters[i].split('=')[1].split('[')[0])
                new_vol = original_vol * vol_mult
                volume_filters[i] = volume_filters[i].replace(f'={original_vol}', f'={new_vol}')
        
        # 모든 화음 믹싱
        all_inputs = [f"[chord{i//3}_{list(chord.keys())[i%3]}]" for i, chord in enumerate(chord_progression) for _ in range(3)]
        
        # 최종 FFmpeg 명령어 구성
        full_filter = f"{''.join(volume_filters)};{''.join(all_inputs[:min(len(all_inputs), 8)])}amix=inputs={min(len(all_inputs), 8)}:duration=longest,{style_config['effects']}"
        
        command = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", ";".join(chord_inputs),
            "-filter_complex", full_filter,
            "-ac", "2",
            "-ar", "44100",
            "-t", str(duration),
            "-y",
            bgm_path
        ]
        
        subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ 🎵 향상된 {style_preference} 스타일 음악적 BGM 생성 성공: {bgm_path}")
        return bgm_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 향상된 BGM 생성 실패: {e.stderr}")
        # 폴백: 간단한 BGM 생성
        return generate_simple_fallback_bgm(duration, style_preference, output_dir)

# 🆕 [새로 추가] 간단한 폴백 BGM 생성 함수
def generate_simple_fallback_bgm(duration: int, style_preference: str, output_dir: str):
    """🎵 간단한 폴백 BGM 생성 (향상된 BGM 실패시)"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bgm_path = os.path.join(output_dir, f"fallback_bgm_{style_preference}_{timestamp}.wav")
    
    # 간단한 설정
    simple_configs = {
        "모던하고 깔끔한": {"freq": 261.63, "volume": 0.2},
        "따뜻하고 아늑한": {"freq": 220.00, "volume": 0.25},
        "미니멀하고 프리미엄한": {"freq": 130.81, "volume": 0.15},
        "역동적이고 에너지": {"freq": 146.83, "volume": 0.3},
        "감성적이고 로맨틱": {"freq": 174.61, "volume": 0.2}
    }
    
    config = simple_configs.get(style_preference, simple_configs["모던하고 깔끔한"])
    
    try:
        command = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"sine=frequency={config['freq']}:duration={duration}",
            "-af", f"volume={config['volume']},aecho=0.7:0.8:500:0.2",
            "-ac", "2",
            "-ar", "44100",
            "-t", str(duration),
            "-y",
            bgm_path
        ]
        
        subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ 간단한 폴백 BGM 생성 성공: {bgm_path}")
        return bgm_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 폴백 BGM 생성도 실패: {e.stderr}")
        return None

# 🆕 [새로 추가] 비디오 길이 확장 함수
def extend_video_to_target_duration(video_path: str, target_duration: int, output_dir: str):
    """CogVideoX 5초 영상을 목표 길이로 확장"""
    if not os.path.exists(video_path):
        raise Exception(f"원본 비디오 파일을 찾을 수 없습니다: {video_path}")
    
    # 현재 영상 길이 확인
    probe_command = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
    try:
        result = subprocess.run(probe_command, capture_output=True, text=True, check=True)
        current_duration = float(result.stdout.strip())
        print(f"🎬 원본 영상 길이: {current_duration:.2f}초")
    except:
        current_duration = 5.0  # 기본값
        print(f"⚠️ 영상 길이 확인 실패, 기본값 {current_duration}초로 가정")
    
    if current_duration >= target_duration:
        print(f"✅ 영상이 이미 목표 길이({target_duration}초)보다 깁니다.")
        return video_path
    
    # 확장된 영상 파일 경로
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extended_path = os.path.join(output_dir, f"extended_{target_duration}sec_{timestamp}.mp4")
    
    # 마지막 프레임을 연장하여 목표 길이 달성
    extend_time = target_duration - current_duration
    
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"tpad=stop_mode=clone:stop_duration={extend_time}",
        "-af", f"apad=pad_dur={extend_time}",
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-y",
        extended_path
    ]
    
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ 영상 확장 성공: {current_duration:.2f}초 → {target_duration}초")
        return extended_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 영상 확장 실패: {e.stderr}")
        raise Exception(f"영상 확장 실패: {e.stderr}")

# 🆕 [수정] 스토리보드에서 CogVideoX용 프롬프트를 추출하는 함수 (개선 버전)
def extract_prompt_from_storyboard(storyboard: Dict[str, Any], brand: str = "", style_preference: str = "") -> str:
    """
    제공된 스토리보드 딕셔너리에서 CogVideoX 텍스트-투-비디오 모델에 사용될 최적화된 프롬프트를 추출합니다.
    """
    if not storyboard or "scenes" not in storyboard: # 스토리보드가 없거나 'scenes' 키가 없으면 기본 프롬프트 반환
        return f"{brand} commercial video with modern and clean style, product showcase"
    
    scenes = storyboard["scenes"] # 스토리보드에서 장면 목록을 가져옵니다.
    if not scenes: # 장면이 없으면 기본 프롬프트 반환
        return f"{brand} commercial video with modern and clean style, product showcase"
    
    # 첫 번째 씬의 description을 우선 사용 (제품이 먼저 나와야 하므로 중요합니다).
    first_scene = scenes[0]
    description = first_scene.get("description", "") # 첫 번째 장면의 시각적 설명을 가져옵니다.
    
    if description: # 설명이 있다면
        # 🚀 개선된 최적화 함수 사용
        optimized = optimize_cogvideo_prompt_enhanced(brand, description, "", style_preference)
        optimized = validate_brand_prompt(brand, optimized)
        return optimized # 최적화된 프롬프트를 반환합니다.
    else: # 설명이 없다면 기본 프롬프트 반환
        return f"{brand} commercial advertisement with {style_preference} style, product showcase"

# 🆕 [새로 추가] 브랜드별 빠른 예시 프리셋 (개선 버전)
BRAND_PRESETS = {
    "애플": {
        "keywords": "iPhone, 혁신적인 기술, 세련된 디자인, 프리미엄, 라이프스타일",
        "style": "미니멀하고 프리미엄한",
        "visual_focus": "iPhone in hands from first frame, premium design, iOS interface"
    },
    "나이키": {
        "keywords": "Just Do It, 러닝화, 스포츠, 도시 조깅, 운동선수",
        "style": "역동적이고 에너지",
        "visual_focus": "Nike shoes closeup first, athlete running, swoosh logo"
    },
    "삼성": {
        "keywords": "Galaxy, 첨단 기술, 스마트폰, 혁신, 미래",
        "style": "모던하고 깔끔한",
        "visual_focus": "Samsung Galaxy phone displayed prominently, tech features"
    },
    "스타벅스": {
        "keywords": "겨울 신메뉴, 따뜻한 커피, 아늑한 분위기, 카페, 바리스타",
        "style": "따뜻하고 아늑한",
        "visual_focus": "Starbucks coffee cup prominent, barista making drink"
    },
    "엔디비아": {
        "keywords": "RTX 그래픽카드, AI 컴퓨팅, 게이밍 기술, 고성능 GPU, 미래 기술",
        "style": "모던하고 깔끔한",
        "visual_focus": "NVIDIA RTX graphics card from first frame, gaming setup with RGB lighting, green LED accents, high-tech computer components"
    }
}

# 이미지와 오디오를 결합하여 하나의 비디오를 생성하는 함수 (FFmpeg 활용)
def generate_video_from_image_and_audio(image_path: str, audio_path: str, output_dir: str):
    """
    이미지 파일과 오디오 파일을 결합하여 MP4 비디오를 생성합니다. (FFmpeg 사용)
    """
    os.makedirs(output_dir, exist_ok=True) # 출력 디렉토리가 없으면 생성합니다.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 현재 시간으로 타임스탬프를 생성합니다.
    output_path = os.path.join(output_dir, f"ad_scene_{timestamp}.mp4") # 출력 비디오 파일 경로를 생성합니다.

    command = [ # FFmpeg 명령어를 리스트 형태로 정의합니다.
        "ffmpeg",
        "-loop", "1", # 이미지를 루프하여 비디오 길이만큼 반복합니다.
        "-i", image_path, # 입력 이미지 파일 경로
        "-i", audio_path, # 입력 오디오 파일 경로
        "-c:v", "libx264", # 비디오 코덱을 H.264로 설정합니다.
        "-tune", "stillimage", # 정지 이미지에 최적화된 튜닝을 적용합니다.
        "-c:a", "aac", # 오디오 코덱을 AAC로 설정합니다.
        "-b:a", "192k", # 오디오 비트레이트를 192kbps로 설정합니다.
        "-pix_fmt", "yuv420p", # 픽셀 형식을 yuv420p로 설정합니다 (일반적인 호환성).
        "-shortest", # 가장 짧은 입력(여기서는 오디오 길이)에 맞춰 출력 길이를 설정합니다.
        "-y", # 출력 파일이 존재하면 덮어씁니다.
        "-vf", "scale=1024:1024", # 비디오 필터: 1024x1024 해상도로 스케일링합니다.
        output_path # 출력 비디오 파일 경로
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # FFmpeg 명령어를 실행합니다.
        print(f"✅ 영상 생성 성공: {output_path}")
        return output_path # 생성된 비디오 파일 경로를 반환합니다.
    except subprocess.CalledProcessError as e: # FFmpeg 명령 실행 실패 시 예외 처리
        print(f"❌ 영상 생성 실패: {e.stderr.decode()}") # FFmpeg 오류 메시지를 출력합니다.
        raise RuntimeError(f"FFmpeg 영상 생성 실패: {e.stderr.decode()}") # 런타임 오류를 발생시킵니다.

# ─────────────────────────────────────────────
# 4) Pydantic 모델 정의
# ─────────────────────────────────────────────

# 기존 광고 생성 요청 모델 (하위 호환성 유지)
class AdGenerationRequest(BaseModel): # FastAPI 요청 본문(body)의 데이터 구조를 정의하는 Pydantic 모델입니다.
    brand: str = Field(..., description="광고할 브랜드명", example="스타벅스") # 브랜드명 (필수, 문자열)
    keywords: List[str] = Field(..., description="광고 내용에 포함될 키워드 리스트", example=["커피", "겨울", "따뜻함"]) # 키워드 목록 (필수, 문자열 리스트)
    target_audience: str = Field(..., description="광고의 타겟 고객층", example="20-30대 직장인") # 타겟 고객층 (필수, 문자열)
    campaign_type: str = Field(default="브랜드 인지도", description="광고 캠페인의 유형", example="브랜드 인지도") # 캠페인 유형 (선택, 기본값 "브랜드 인지도")
    style_preference: str = Field(default="모던하고 깔끔한", description="광고의 시각적/전반적인 스타일 선호도", example="모던하고 깔끔한") # 스타일 선호도 (선택, 기본값 "모던하고 깔끔한")
    duration: int = Field(default=30, description="생성될 광고의 총 길이 (초 단위)", example=30, ge=15, le=120) # 광고 길이 (선택, 기본값 30초, 15초 이상 120초 이하)

    # 음성(내레이션) 생성 옵션
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field( # TTS에 사용될 음성 모델 (고정된 선택지 중 하나)
        default="alloy",
        description="텍스트-음성 변환(TTS)에 사용될 음성 모델 선택"
    )

    # 음성 품질 검증 옵션
    enable_quality_validation: bool = Field( # 음성 품질 검증 활성화 여부
        default=True,
        description="Whisper 모델 기반의 생성된 음성 품질 검증 활성화 여부"
    )
    min_quality_score: float = Field( # 음성 품질 최소 점수
        default=0.8,
        description="음성이 '품질 기준 통과'로 간주될 최소 품질 점수 (0.0~1.0 사이)",
        ge=0.0, # 0.0 이상
        le=1.0 # 1.0 이하
    )
    max_retry_attempts: int = Field( # 음성 생성 재시도 최대 횟수
        default=2,
        description="음성 품질 기준 미달 시 내레이션 재시도 최대 횟수",
        ge=0, # 0 이상
        le=5 # 5 이하
    )

    # 비디오 생성 옵션
    enable_cogvideo: bool = Field( # CogVideoX 비디오 생성 기능 활성화 여부
        default=True,
        description="CogVideoX 텍스트-투-비디오 생성 기능 활성화 여부"
    )

    class Config: # Pydantic 모델의 추가 설정
        json_schema_extra = { # API 문서(Swagger UI)에 표시될 예시 JSON
            "example": {
                "brand": "스타벅스",
                "keywords": ["커피", "겨울", "따뜻함", "신메뉴"],
                "target_audience": "20-30대 직장인",
                "campaign_type": "브랜드 인지도",
                "style_preference": "모던하고 깔끔한",
                "duration": 30,
                "voice": "nova",
                "enable_quality_validation": True,
                "min_quality_score": 0.8,
                "max_retry_attempts": 2,
                "enable_cogvideo": True
            }
        }

# 새로운 완전 통합 광고 생성 요청 모델
class CompleteAdRequest(BaseModel): # 새로운 완전 통합 광고 생성을 위한 Pydantic 모델입니다.
    brand: str = Field(..., description="브랜드명") # 브랜드명 (필수)
    keywords: str = Field(..., description="키워드 또는 문장 (자유 형식)") # 키워드 (필수, 자유 형식 문자열)

    # 선택적 설정
    target_audience: str = Field(default="일반 소비자", description="타겟 고객층") # 타겟 고객층 (선택, 기본값 "일반 소비자")
    style_preference: str = Field(default="모던하고 깔끔한", description="영상 스타일") # 영상 스타일 (선택, 기본값 "모던하고 깔끔한")
    duration: int = Field(default=30, description="영상 길이(초)", ge=15, le=60) # 영상 길이 (선택, 기본값 30초, 15초 이상 60초 이하)

    # 품질 설정
    video_quality: Literal["fast", "balanced", "high"] = Field(default="balanced") # 비디오 품질 (선택, "fast", "balanced", "high" 중 하나)
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(default="nova") # TTS 음성 모델 (고정된 선택지 중 하나)

    # 추가 옵션
    enable_bgm: bool = Field(default=True, description="BGM 생성 활성화") # BGM 생성 활성화 여부 (선택, 기본값 True)
    bgm_style: str = Field(default="auto", description="BGM 스타일") # BGM 스타일 (선택, 기본값 "auto")

    class Config: # Pydantic 모델의 추가 설정
        json_schema_extra = { # API 문서(Swagger UI)에 표시될 예시 JSON
            "example": {
                "brand": "엔디비아",
                "keywords": "RTX 그래픽카드, 게이밍 성능, AI 컴퓨팅",
                "target_audience": "게이머 및 크리에이터",
                "style_preference": "모던하고 깔끔한",
                "duration": 30,
                "video_quality": "balanced",
                "voice": "nova",
                "enable_bgm": True,
                "bgm_style": "auto"
            }
        }

# 응답 모델들
class TaskResponse(BaseModel): # 작업 시작 시 반환되는 응답 모델
    task_id: str # 생성된 작업의 고유 ID
    status: str # 작업의 현재 상태 (예: "queued")
    message: str # 사용자에게 표시될 메시지

class TaskStatusResponse(BaseModel): # 작업 상태 조회 시 반환되는 응답 모델
    task_id: str # 작업 ID
    status: str # 작업의 현재 상태 (예: "processing", "completed", "failed")
    progress: int # 작업 진행률 (0-100)
    current_step: str # 현재 진행 중인 단계 설명
    estimated_completion: Optional[str] = None # 예상 완료 시간 (선택 사항)
    error: Optional[str] = None # 오류 메시지 (작업 실패 시)

class QualityValidationSettings(BaseModel): # 품질 검증 설정 조회 시 반환되는 응답 모델
    whisper_available: bool # Whisper 모델 가용성 여부
    supported_models: List[str] # 지원되는 Whisper 모델 목록
    default_settings: Dict[str, Any] # 기본 품질 검증 설정

# ─────────────────────────────────────────────
# 5) API 엔드포인트 정의 (루트 및 헬스 체크)
# ─────────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False) # /favicon.ico 경로에 대한 GET 요청 처리, API 문서에 포함되지 않습니다.
async def favicon():
    """서버의 루트 디렉토리에 위치한 favicon.ico 파일을 반환합니다."""
    return FileResponse(Path(__file__).parent / "favicon.ico") # 현재 파일이 있는 디렉토리의 favicon.ico 파일을 반환합니다.

@app.get("/", response_class=HTMLResponse) # 루트 경로(/)에 대한 GET 요청 처리, HTML 응답을 반환합니다.
async def serve_frontend(request: Request):
    """메인 웹 인터페이스 제공"""
    # 새로운 complete_ad_creator.html이 있으면 사용, 없으면 기본 HTML 반환
    try:
        # Jinja2 템플릿을 사용하여 complete_ad_creator.html 파일을 렌더링하여 응답합니다.
        return templates.TemplateResponse("complete_ad_creator.html", {"request": request})
    except Exception: # 템플릿 파일이 없거나 오류 발생 시
        # templates 폴더가 없거나 파일이 없으면 기본 HTML을 직접 반환합니다.
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 광고 크리에이터 v3.1</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .info { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .api-link { display: block; text-align: center; background: #667eea; color: white; padding: 15px; border-radius: 10px; text-decoration: none; margin: 10px 0; }
        .api-link:hover { background: #5a6fd8; }
        .feature { color: #28a745; font-weight: bold; }
        .new-feature { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 광고 크리에이터 v3.1</h1>
        <div class="info">
            <h3>📋 사용 가능한 기능</h3>
            <ul>
                <li>✅ CogVideoX AI 영상 생성</li>
                <li>✅ OpenAI TTS 나레이션</li>
                <li class="new-feature">🆕 향상된 음악적 BGM 생성</li>
                <li class="new-feature">🆕 브랜드별 최적화 프롬프트</li>
                <li class="feature">🎵 화음 기반 BGM 자동 생성</li>
                <li class="feature">🎬 30초 완성 광고 자동 생성</li>
                <li>✅ FFmpeg 영상 합성</li>
            </ul>
        </div>
        <a href="/docs" class="api-link">📚 API 문서 (Swagger UI)</a>
        <a href="/health" class="api-link">🔍 시스템 상태 확인</a>
        <div class="info">
            <h3>🚀 빠른 시작</h3>
            <p>1. <strong>/docs</strong>에서 API 문서 확인</p>
            <p>2. <strong>POST /api/v1/ads/create-complete</strong>로 30초 완성 광고 생성</p>
            <p>3. <strong>GET /api/v1/ads/status/{task_id}</strong>로 진행상황 확인</p>
            <p>4. <strong>GET /download/{task_id}</strong>로 완성된 영상 다운로드</p>
        </div>
        <div class="info">
            <h3>🎯 NEW! v3.1 개선사항</h3>
            <p>• <span class="new-feature">🎵 화음 기반 음악적 BGM</span> - 코드 진행과 리듬 패턴</p>
            <p>• <span class="new-feature">🎬 브랜드별 최적화</span> - 엔디비아, 애플 등 브랜드 특화</p>
            <p>• <span class="new-feature">🔍 품질 검증 강화</span> - 자동 프롬프트 보완</p>
            <p>• <span class="feature">⚡ 폴백 시스템</span> - 안정성 향상</p>
        </div>
    </div>
</body>
</html>
        """, status_code=200) # 기본 HTML 응답 (상태 코드 200)

def get_available_whisper_models():
    """시스템에 로드 가능한 Whisper 모델 목록을 동적으로 조회하여 반환합니다."""
    try:
        import whisper # whisper 라이브러리 임포트를 시도합니다.
        available = whisper.available_models() # 사용 가능한 Whisper 모델 목록을 가져옵니다.
        return sorted(list(available)) # 정렬된 리스트로 반환합니다.
    except ImportError: # whisper 라이브러리가 없으면
        return [] # 빈 리스트 반환
    except Exception as e: # 그 외 예외 발생 시
        print(f"Warning: whisper.available_models() 조회 오류: {e}")
        return ["tiny", "base", "small", "medium", "large"] # 기본 모델 목록 반환

def check_ffmpeg_availability():
    """시스템에 FFmpeg가 설치되어 있고 실행 가능한지 확인합니다."""
    try:
        # 'ffmpeg -version' 명령어를 실행하여 FFmpeg 설치 여부를 확인합니다.
        result = subprocess.run(['ffmpeg', '-version'],
                                 capture_output=True, text=True, timeout=10) # 출력 캡처, 텍스트 모드, 10초 타임아웃
        return result.returncode == 0 # 종료 코드가 0이면 성공 (설치됨)
    except Exception: # 명령어 실행 중 오류 발생 시 (예: FFmpeg가 PATH에 없거나 설치되지 않음)
        return False # False 반환

@app.get("/health") # /health 경로에 대한 GET 요청 처리
async def health_check():
    """API 서버의 전반적인 상태 확인"""
    
    # Whisper 가용성 확인
    whisper_available = False
    whisper_error = None
    supported_models = []
    
    try:
        import whisper # Whisper 라이브러리 임포트 시도
        whisper_available = True
        supported_models = get_available_whisper_models() # 사용 가능한 Whisper 모델 목록 가져오기
    except Exception as e:
        whisper_error = str(e) # 오류 메시지 저장
        supported_models = []
    
    # librosa 가용성 확인 (오디오 품질 분석용)
    librosa_available = False
    try:
        import librosa # librosa 라이브러리 임포트 시도
        librosa_available = True
    except Exception:
        pass
    
    # FFmpeg 가용성 확인
    ffmpeg_available = check_ffmpeg_availability()
    
    return { # 서버 상태를 JSON 형식으로 반환
        "status": "healthy", # 전체 서버 상태
        "version": "3.1.0", # API 버전
        "timestamp": datetime.now().isoformat(), # 현재 시간
        "services": { # 개별 서비스의 상태
            "api": "running",
            "ai_workflow": "ready" if WORKFLOW_AVAILABLE else "unavailable", # AI 워크플로우 상태
            "task_storage": "ready",
            "openai_api": "ready" if os.getenv("OPENAI_API_KEY") else "no_api_key", # OpenAI API 키 설정 여부
            "whisper_quality_validation": "ready" if whisper_available else "unavailable", # Whisper 기반 품질 검증 상태
            "audio_quality_analysis": "ready" if librosa_available else "unavailable", # librosa 기반 오디오 분석 상태
            "ffmpeg_video_composition": "ready" if ffmpeg_available else "unavailable", # FFmpeg 비디오 합성 상태
            "cogvideo_text_to_video": "ready" if COGVIDEO_AVAILABLE else "unavailable", # CogVideoX 텍스트-투-비디오 상태
            "riffusion_bgm": "ready" if RIFFUSION_AVAILABLE else "unavailable", # Riffusion BGM 상태
            "enhanced_musical_bgm": "ready" if ffmpeg_available else "unavailable" # 🆕 향상된 음악적 BGM 상태
        },
        "capabilities": { # 서버의 기능 가용성 요약
            "video_generation": COGVIDEO_AVAILABLE,
            "voice_generation": bool(os.getenv("OPENAI_API_KEY")),
            "enhanced_bgm_generation": ffmpeg_available,  # 🆕 향상된 BGM 생성
            "brand_optimization": True,  # 🆕 브랜드별 최적화
            "video_composition": ffmpeg_available,
            "video_extension": ffmpeg_available,
            "complete_30sec_workflow": all([
                COGVIDEO_AVAILABLE,
                os.getenv("OPENAI_API_KEY"),
                ffmpeg_available
            ])
        },
        "video_composition": { # 비디오 합성 관련 상세 정보
            "ffmpeg_available": ffmpeg_available,
            "cogvideo_available": COGVIDEO_AVAILABLE,
            "cogvideo_legacy_available": COGVIDEO_LEGACY_AVAILABLE,
            "supported_resolutions": ["1920x1080", "1280x720", "854x480"],
            "supported_formats": ["mp4", "avi", "mov"],
            "default_video_quality": "medium",
            "video_extension_supported": ffmpeg_available
        },
        "quality_validation": { # 품질 검증 관련 상세 정보
            "whisper_available": whisper_available,
            "whisper_error": whisper_error,
            "librosa_available": librosa_available,
            "supported_whisper_models": supported_models,
            "total_available_models": len(supported_models),
            "default_quality_threshold": 0.8
        },
        "bgm_generation": { # BGM 생성 관련 상세 정보
            "riffusion_available": RIFFUSION_AVAILABLE,
            "enhanced_musical_bgm_available": ffmpeg_available,  # 🆕 향상된 음악적 BGM
            "chord_based_harmonies": ffmpeg_available,  # 🆕 화음 기반 생성
            "supported_styles": ["모던하고 깔끔한", "따뜻하고 아늑한", "미니멀하고 프리미엄한", "역동적이고 에너지", "감성적이고 로맨틱"],
            "fallback_system": True,  # 🆕 폴백 시스템
            "default_bgm_volume": 0.25
        },
        "brand_optimization": {  # 🆕 브랜드 최적화 정보
            "supported_brands": list(BRAND_PRESETS.keys()),
            "enhanced_prompts": True,
            "brand_validation": True,
            "visual_scenarios": True
        },
        "active_tasks": len([t for t in tasks_storage.values() if t["status"] == "processing"]), # 현재 처리 중인 작업 수
        "total_completed_tasks": len([t for t in tasks_storage.values() if t["status"] == "completed"]) # 총 완료된 작업 수
    }

@app.get("/api/v1/video/ffmpeg-status") # /api/v1/video/ffmpeg-status 경로에 대한 GET 요청 처리
async def get_ffmpeg_status():
    """FFmpeg 설치 상태 확인"""
    ffmpeg_available = check_ffmpeg_availability()
    
    return {
        "ffmpeg_available": ffmpeg_available,
        "cogvideo_available": COGVIDEO_AVAILABLE,
        "enhanced_bgm_available": ffmpeg_available,  # 🆕 향상된 BGM 가용성
        "install_guide": {
            "windows": "winget install --id=Gyan.FFmpeg -e 또는 choco install ffmpeg (관리자 권한)",
            "macos": "brew install ffmpeg (Homebrew 설치 필요)",
            "ubuntu": "sudo apt update && sudo apt install ffmpeg",
            "conda": "conda install -c conda-forge ffmpeg (Conda 환경 내)"
        },
        "test_command": "ffmpeg -version",
        "message": "FFmpeg 사용 가능 (향상된 BGM 지원)" if ffmpeg_available else "FFmpeg가 설치되지 않았습니다. 위의 가이드를 참조하여 설치해주세요."
    }

# ─────────────────────────────────────────────
# 6) 품질 검증 관련 엔드포인트들
# ─────────────────────────────────────────────
@app.get("/api/v1/quality/settings", response_model=QualityValidationSettings)
async def get_quality_validation_settings():
    """음성 품질 검증 시스템의 현재 설정 및 가용성 정보를 조회합니다."""
    
    whisper_available = False
    supported_models = []
    try:
        import whisper
        whisper_available = True
        supported_models = ["tiny", "base", "small", "medium", "large"]
    except Exception:
        pass
    
    return QualityValidationSettings(
        whisper_available=whisper_available,
        supported_models=supported_models,
        default_settings={
            "min_quality_score": 0.8,
            "max_retry_attempts": 2,
            "whisper_model": "base",
            "enable_quality_validation": True,
            "quality_analysis_available": whisper_available
        }
    )

@app.post("/api/v1/quality/test")
async def test_quality_validation(test_text: str = "안녕하세요. 테스트 음성입니다."):
    """음성 품질 검증 시스템의 작동 여부를 테스트합니다."""
    
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="OpenAI API 키가 설정되지 않았습니다.")
    
    try:
        from app.agents.agents import EnhancedAudioGeneratorAgent
        
        test_dir = os.path.join(os.getcwd(), "test_audio")
        os.makedirs(test_dir, exist_ok=True)
        
        test_agent = EnhancedAudioGeneratorAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            audio_dir=test_dir,
            enable_quality_validation=True,
            max_retry_attempts=1
        )
        
        test_storyboard = {
            "scenes": [
                {
                    "name": "Test Scene",
                    "narration": test_text,
                    "description": "Quality validation test"
                }
            ]
        }
        
        result = test_agent.generate_narrations_with_validation(
            test_storyboard, 
            voice="alloy",
            min_quality_score=0.7
        )
        
        if result and result[0].get("file") and os.path.exists(result[0]["file"]):
            os.remove(result[0]["file"])
        
        return {
            "test_successful": True,
            "message": "품질 검증 시스템이 정상 작동합니다.",
            "test_result": {
                "audio_generated": bool(result and result[0].get("file")),
                "quality_validated": bool(result and result[0].get("quality_validation", {}).get("available")),
                "quality_score": result[0].get("quality_validation", {}).get("overall_score", 0) if result else 0,
                "test_text": test_text
            }
        }
        
    except Exception as e:
        return {
            "test_successful": False,
            "error": str(e),
            "message": "품질 검증 시스템 테스트 실패"
        }

# ─────────────────────────────────────────────
# 7) 광고 생성 백그라운드 작업들
# ─────────────────────────────────────────────

# 🆕 [수정] 기존 광고 생성 워크플로우 - 개선된 프롬프트 적용
async def process_ad_generation(task_id: str, request_data: dict):
    """기존 광고 생성 워크플로우 (이미지 + 음성 + 비디오) - 개선된 프롬프트 적용"""
    try:
        if ai_workflow is None:
            initialize_workflow()
        
        tasks_storage[task_id].update(status="processing", progress=5, current_step="AI 워크플로우 초기화 중...")

        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            print(f"✅ process_ad_generation: API Key 확인 - {api_key[:5]}...")
        else:
            print("❌ process_ad_generation: API Key를 찾을 수 없음")

        # Step 1: 광고 컨셉 생성 (5% → 20%)
        tasks_storage[task_id].update(progress=10, current_step="광고 컨셉 생성 중...")
        
        from app.agents.agents import ConceptGeneratorAgent, ImageGeneratorAgent, EnhancedAudioGeneratorAgent
        concept_agent = ConceptGeneratorAgent(PROMPT_TEMPLATE, api_key=api_key)

        keywords_str = ", ".join(request_data["keywords"])
        storyboard = concept_agent.generate_concept(
            request_data["brand"],
            keywords_str,
            request_data.get("campaign_type", "브랜드 인지도"),
            request_data.get("style_preference", "모던하고 깔끔한")
        )
        tasks_storage[task_id]["storyboard"] = storyboard
        tasks_storage[task_id].update(progress=20, current_step="컨셉 생성 완료")

        # Step 2: 이미지 생성 (20% → 45%)
        tasks_storage[task_id].update(progress=25, current_step="광고 이미지 생성 중...")
        images_dir = os.path.join(os.getcwd(), "generated/images")
        image_agent = ImageGeneratorAgent(openai_api_key=api_key, images_dir=images_dir)
        
        tasks_storage[task_id]["images"] = image_agent.generate_images(
            storyboard,
            request_data.get("style_preference", "모던하고 깔끔한")
        )
        tasks_storage[task_id].update(progress=45, current_step="이미지 생성 완료")

        # Step 3: 품질 검증을 포함한 음성 생성 (45% → 70%)
        tasks_storage[task_id].update(progress=50, current_step="고품질 내레이션 음성 생성 중...")
        
        audio_dir = os.path.join(os.getcwd(), "generated/audio")
        
        quality_options = {
            "enable_quality_validation": request_data.get("enable_quality_validation", True),
            "max_retry_attempts": request_data.get("max_retry_attempts", 2),
            "min_quality_score": request_data.get("min_quality_score", 0.8)
        }
        
        enhanced_audio_agent = EnhancedAudioGeneratorAgent(
            openai_api_key=api_key, 
            audio_dir=audio_dir,
            enable_quality_validation=quality_options["enable_quality_validation"],
            max_retry_attempts=quality_options["max_retry_attempts"]
        )
        
        voice_option = request_data.get("voice", "alloy")
        
        validated_audio_result = enhanced_audio_agent.generate_narrations_with_validation(
            storyboard, 
            voice=voice_option,
            min_quality_score=quality_options["min_quality_score"]
        )
        
        if validated_audio_result is None:
            validated_audio_result = []
            tasks_storage[task_id]["validated_audio"] = []
        else:
            tasks_storage[task_id]["validated_audio"] = validated_audio_result
        
        tasks_storage[task_id].update(progress=70, current_step="음성 품질 검증 완료")

        # Step 4: 품질 리포트 생성 (70% → 75%)
        tasks_storage[task_id].update(progress=72, current_step="품질 리포트 생성 중...")
        
        quality_report = generate_quality_report(tasks_storage[task_id]["validated_audio"])
        tasks_storage[task_id]["quality_report"] = quality_report
        tasks_storage[task_id].update(progress=75, current_step="품질 분석 완료")

        # Step 5: 🆕 [수정] 개선된 비디오 생성 (75% → 90%)
        tasks_storage[task_id].update(progress=78, current_step="비디오 생성 중...")
        
        video_paths = []
        
        # CogVideoX 사용 시도 (신규 또는 레거시)
        if (COGVIDEO_AVAILABLE or COGVIDEO_LEGACY_AVAILABLE) and request_data.get("enable_cogvideo", True):
            try:
                tasks_storage[task_id].update(progress=80, current_step="CogVideoX AI 비디오 생성 중...")
                
                # 🎯 [수정] 개선된 프롬프트 추출 함수 사용
                video_prompt = extract_prompt_from_storyboard(
                    storyboard, 
                    brand=request_data["brand"], 
                    style_preference=request_data.get("style_preference", "모던하고 깔끔한")
                )
                print(f"🎬 개선된 CogVideoX 프롬프트: {video_prompt}")
                
                video_dir = os.path.join(os.getcwd(), "generated", "videos", task_id)
                os.makedirs(video_dir, exist_ok=True)
                
                # 신규 CogVideoX 사용 시도
                if COGVIDEO_AVAILABLE:
                    generator = CogVideoXGenerator(output_dir=video_dir)
                    cogvideo_path = generator.generate_video_from_prompt(
                        prompt=video_prompt,
                        quality="balanced"
                    )
                # 레거시 CogVideoX 사용
                elif COGVIDEO_LEGACY_AVAILABLE:
                    cogvideo_path = generate_with_cogvideo(
                        prompt=video_prompt,
                        output_dir=video_dir,
                        num_frames=120,
                        num_inference_steps=30
                    )
                else:
                    cogvideo_path = None
                
                if cogvideo_path and os.path.exists(cogvideo_path):
                    video_paths = [cogvideo_path]
                    tasks_storage[task_id].update(progress=88, current_step="CogVideoX 비디오 생성 완료")
                    print(f"✅ CogVideoX 비디오 생성 성공: {cogvideo_path}")
                else:
                    raise Exception("CogVideoX 비디오 생성 실패")
                    
            except Exception as e:
                print(f"❌ CogVideoX 비디오 생성 실패: {e}")
                print("🔄 FFmpeg 이미지+오디오 합성 방식으로 폴백합니다...")
                
                # 폴백: 기존 이미지+오디오 합성 방식
                tasks_storage[task_id].update(progress=82, current_step="이미지+오디오 합성 비디오 생성 중...")
                video_dir = os.path.join(os.getcwd(), "generated/videos")
                
                for idx, (image_info, audio_info) in enumerate(
                        zip(tasks_storage[task_id]["images"], 
                            tasks_storage[task_id]["validated_audio"])):
                    
                    img_path = image_info["file"] if isinstance(image_info, dict) else image_info
                    aud_path = audio_info["file"]
                    
                    if img_path and aud_path and os.path.exists(img_path) and os.path.exists(aud_path):
                        try:
                            video_path = generate_video_from_image_and_audio(img_path, aud_path, video_dir)
                            video_paths.append(video_path)
                        except Exception as inner_e:
                            print(f"❌ 씬 {idx+1} 비디오 합성 실패: {inner_e}")
                            continue
                
                tasks_storage[task_id].update(progress=88, current_step="폴백 비디오 생성 완료")
        else:
            # CogVideoX 비활성화 시 이미지+오디오 합성
            tasks_storage[task_id].update(progress=80, current_step="이미지+오디오 합성 비디오 생성 중...")
            video_dir = os.path.join(os.getcwd(), "generated/videos")
            
            for idx, (image_info, audio_info) in enumerate(
                    zip(tasks_storage[task_id]["images"], 
                        tasks_storage[task_id]["validated_audio"])):
                
                img_path = image_info["file"] if isinstance(image_info, dict) else image_info
                aud_path = audio_info["file"]
                
                if img_path and aud_path and os.path.exists(img_path) and os.path.exists(aud_path):
                    try:
                        video_path = generate_video_from_image_and_audio(img_path, aud_path, video_dir)
                        video_paths.append(video_path)
                    except Exception as inner_e:
                        print(f"❌ 씬 {idx+1} 비디오 합성 실패: {inner_e}")
                        continue
            
            tasks_storage[task_id].update(progress=88, current_step="이미지+오디오 비디오 생성 완료")

        tasks_storage[task_id]["videos"] = video_paths
        tasks_storage[task_id].update(progress=90, current_step="비디오 생성 완료")

        # Step 6: 워크플로우 통합 및 최종 검사 (90% → 100%)
        tasks_storage[task_id].update(progress=92, current_step="최종 품질 검사 및 결과 통합 중...")
        
        workflow_input = {
            "brand": request_data["brand"],
            "keywords": keywords_str,
            "target_audience": request_data["target_audience"],
            "duration": request_data.get("duration", 30),
            "campaign_type": request_data.get("campaign_type", "브랜드 인지도"),
            "style_preference": request_data.get("style_preference", "모던하고 깔끔한"),
            "voice": voice_option,
            "quality_options": quality_options,
            "concept": storyboard,
            "images": tasks_storage[task_id]["images"],
            "validated_audio": tasks_storage[task_id]["validated_audio"],
            "quality_report": quality_report,
            "videos": video_paths
        }
        
        if ai_workflow:
            result = ai_workflow.process(workflow_input)
        else:
            result = {
                "status": "completed",
                "message": "멀티모달 광고 콘텐츠가 품질 검증과 함께 성공적으로 생성되었습니다.",
                "content": {
                    "storyboard": storyboard,
                    "images": tasks_storage[task_id]["images"],
                    "validated_audio": tasks_storage[task_id]["validated_audio"],
                    "quality_report": quality_report,
                    "videos": video_paths
                },
                "metadata": {
                    "total_scenes": len(storyboard.get("scenes", [])) if storyboard else 0,
                    "total_images": len(tasks_storage[task_id]["images"]) if tasks_storage[task_id].get("images") else 0,
                    "total_audio_files": len(tasks_storage[task_id]["validated_audio"]) if tasks_storage[task_id].get("validated_audio") else 0,
                    "total_videos": len(video_paths),
                    "cogvideo_used": (COGVIDEO_AVAILABLE or COGVIDEO_LEGACY_AVAILABLE) and request_data.get("enable_cogvideo", True),
                    "quality_validation_enabled": quality_options["enable_quality_validation"],
                    "voice_used": voice_option,
                    "generation_time": datetime.now().isoformat(),
                    "quality_summary": quality_report.get("summary", {}) if quality_report else {}
                }
            }

        tasks_storage[task_id].update(
            status="completed",
            progress=100,
            current_step="완료",
            result=result,
            completed_at=datetime.now().isoformat()
        )
        print(f"✅ 작업 완료 (품질 검증 포함): {task_id}")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()

        tasks_storage[task_id].update(
            status="failed", 
            error=str(e),
            current_step="실패",
            error_details=error_details[:1000]
        )
        print(f"❌ 작업 실패: {task_id} - {e}")

# 🆕 [완전 수정] 30초 완성 광고 생성 워크플로우 (개선 버전)!
async def process_complete_ad_generation(task_id: str, request_data: dict):
    """🚀 30초 완성 광고 생성 워크플로우 (CogVideoX + 확장 + TTS + 향상된 BGM)"""
    try:
        tasks_storage[task_id].update(
            status="processing", 
            progress=5, 
            current_step="30초 완성 광고 생성 시작..."
        )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        brand = request_data["brand"]
        keywords = request_data["keywords"]
        style_preference = request_data.get("style_preference", "모던하고 깔끔한")
        video_quality = request_data.get("video_quality", "balanced")
        voice = request_data.get("voice", "nova")
        duration = request_data.get("duration", 30)
        enable_bgm = request_data.get("enable_bgm", True)
        
        # Step 1: 광고 컨셉 생성 (5% → 15%)
        tasks_storage[task_id].update(progress=10, current_step="브랜드 맞춤 광고 컨셉 생성 중...")
        
        import openai
        
        concept_prompt = get_complete_ad_concept_prompt(
            brand=brand, 
            keywords=keywords, 
            target_audience=request_data.get('target_audience', '일반 소비자'),
            style_preference=style_preference, 
            duration=duration
        )
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": concept_prompt}],
            temperature=0.7
        )
        
        try:
            ad_concept = json.loads(response.choices[0].message.content)
        except:
            preset = BRAND_PRESETS.get(brand, {
                "keywords": keywords,
                "style": style_preference,
                "visual_focus": f"{brand} product showcase from first frame"
            })
            
            ad_concept = {
                "narration": f"{brand}와 함께하는 특별한 순간. {keywords}로 당신의 일상을 더욱 풍요롭게 만들어보세요.",
                "visual_description": f"{preset.get('visual_focus', f'{brand} product showcase')}, {style_preference} style, professional advertisement"
            }
        
        tasks_storage[task_id]["ad_concept"] = ad_concept
        tasks_storage[task_id].update(progress=15, current_step="브랜드 맞춤 컨셉 생성 완료")
        
        print(f"🎯 생성된 나레이션: {ad_concept['narration']}")
        print(f"🎬 생성된 영상 설명: {ad_concept['visual_description']}")
        
        # Step 2: TTS 나레이션 생성 (15% → 25%)
        tasks_storage[task_id].update(progress=20, current_step="나레이션 음성 생성 중...")
        
        narration_text = ad_concept["narration"]
        audio_dir = os.path.join(os.getcwd(), "generated", "audio", task_id)
        os.makedirs(audio_dir, exist_ok=True)
        
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=narration_text
        )
        
        audio_path = os.path.join(audio_dir, f"narration_{task_id}.mp3")
        audio_response.stream_to_file(audio_path)
        
        tasks_storage[task_id]["narration_audio"] = audio_path
        tasks_storage[task_id].update(progress=25, current_step="나레이션 생성 완료")
        
        # Step 3: CogVideoX 영상 생성 (25% → 45%)
        if not COGVIDEO_AVAILABLE:
            raise Exception("CogVideoX가 설치되지 않았습니다.")
        
        tasks_storage[task_id].update(progress=30, current_step="AI 영상 생성 중... (수 분 소요)")
        
        video_dir = os.path.join(os.getcwd(), "generated", "videos", task_id)
        generator = CogVideoXGenerator(output_dir=video_dir)
        
        # 🚀 개선된 프롬프트 최적화 적용
        optimized_prompt = optimize_cogvideo_prompt_enhanced(
            brand=brand,
            visual_description=ad_concept['visual_description'],
            keywords=keywords,
            style_preference=style_preference
        )
        
        # 🔍 브랜드 필수 요소 검증
        optimized_prompt = validate_brand_prompt(brand, optimized_prompt)
        
        print(f"🎬 최적화된 CogVideoX 프롬프트: {optimized_prompt}")
        
        # CogVideoX는 기본적으로 5초 영상만 생성
        original_video_path = generator.generate_video_from_prompt(
            prompt=optimized_prompt,
            duration=5,  # 🔥 CogVideoX는 5초로 고정
            quality=video_quality
        )
        
        if not original_video_path:
            raise Exception("CogVideoX 영상 생성에 실패했습니다.")
        
        tasks_storage[task_id]["original_video"] = original_video_path
        tasks_storage[task_id].update(progress=45, current_step="AI 영상 생성 완료")
        
        # Step 4: 🚀 [핵심] 5초 영상을 30초로 확장 (45% → 60%)
        tasks_storage[task_id].update(progress=50, current_step=f"5초 영상을 {duration}초로 확장 중...")
        
        extended_video_path = extend_video_to_target_duration(
            video_path=original_video_path,
            target_duration=duration,
            output_dir=video_dir
        )
        
        tasks_storage[task_id]["extended_video"] = extended_video_path
        tasks_storage[task_id].update(progress=60, current_step=f"{duration}초 영상 확장 완료")
        
        # Step 5: 🎵 향상된 음악적 BGM 생성 (60% → 75%)
        bgm_path = None
        if enable_bgm:
            tasks_storage[task_id].update(progress=65, current_step="향상된 음악적 BGM 생성 중...")
            
            try:
                bgm_dir = os.path.join(os.getcwd(), "generated", "bgm", task_id)
                
                if RIFFUSION_AVAILABLE:
                    # Riffusion 사용
                    from app.utils.riffusion_utils import BGMGenerator
                    bgm_generator = BGMGenerator(bgm_dir)
                    
                    dummy_storyboard = {
                        "scenes": [{
                            "description": f"{brand} commercial with {keywords}",
                            "narration": narration_text
                        }]
                    }
                    
                    bgm_path = bgm_generator.generate_bgm_for_ad(
                        dummy_storyboard,
                        style_preference=style_preference,
                        duration=duration
                    )
                    print("✅ Riffusion BGM 생성 완료")
                    
                else:
                    # 🚀 향상된 음악적 BGM 생성 (화음 기반)
                    bgm_path = generate_enhanced_musical_bgm(
                        duration=duration,
                        style_preference=style_preference,
                        output_dir=bgm_dir
                    )
                    print("✅ 향상된 음악적 BGM 생성 완료")
                
                tasks_storage[task_id]["bgm_audio"] = bgm_path
                tasks_storage[task_id].update(progress=75, current_step="향상된 BGM 생성 완료")
                
            except Exception as bgm_error:
                print(f"⚠️ BGM 생성 실패: {bgm_error}")
                bgm_path = None
                tasks_storage[task_id].update(progress=75, current_step="BGM 생성 실패, 영상 합성 계속")
        else:
            tasks_storage[task_id].update(progress=75, current_step="BGM 생성 건너뛰기")
        
        # Step 6: 🎬 최종 30초 완성 영상 합성 (75% → 95%)
        tasks_storage[task_id].update(progress=80, current_step="30초 완성 영상 합성 중...")
        
        final_video_dir = os.path.join(os.getcwd(), "generated", "final", task_id)
        os.makedirs(final_video_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(final_video_dir, f"complete_30sec_ad_{brand}_{timestamp}.mp4")
        
        if bgm_path and os.path.exists(bgm_path):
            # 확장된 영상 + 나레이션 + BGM 3중 합성
            tasks_storage[task_id].update(progress=85, current_step="영상 + 나레이션 + 향상된 BGM 완벽 합성 중...")
            
            command = [
                "ffmpeg",
                "-i", extended_video_path,  # 확장된 30초 영상
                "-i", audio_path,           # 나레이션
                "-i", bgm_path,             # 향상된 BGM
                "-filter_complex", 
                "[1:a]volume=1.0[narration];[2:a]volume=0.12[bgm];[narration][bgm]amix=inputs=2:duration=first:dropout_transition=2[audio]",
                "-map", "0:v",
                "-map", "[audio]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-t", str(duration),
                "-y",
                final_video_path
            ]
        else:
            # 확장된 영상 + 나레이션만 합성
            tasks_storage[task_id].update(progress=85, current_step="영상 + 나레이션 합성 중...")
            
            command = [
                "ffmpeg",
                "-i", extended_video_path,  # 확장된 30초 영상
                "-i", audio_path,           # 나레이션
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v",
                "-map", "1:a",
                "-t", str(duration),
                "-shortest",
                "-y",
                final_video_path
            ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        if not os.path.exists(final_video_path):
            raise Exception("최종 영상 합성에 실패했습니다.")
        
        file_size = os.path.getsize(final_video_path) / (1024*1024)
        
        tasks_storage[task_id]["final_video"] = final_video_path
        tasks_storage[task_id].update(progress=95, current_step="30초 완성 영상 합성 완료")
        
        # Step 7: 결과 정리 (95% → 100%)
        tasks_storage[task_id].update(progress=98, current_step="결과 정리 중...")
        
        result = {
            "status": "completed",
            "message": f"🎉 {brand} 브랜드 30초 완성 광고가 성공적으로 생성되었습니다!",
            "content": {
                "brand": brand,
                "keywords": keywords,
                "narration_text": narration_text,
                "narration_audio": audio_path,
                "original_video": original_video_path,
                "extended_video": extended_video_path,
                "bgm_audio": bgm_path,
                "final_video": final_video_path
            },
            "metadata": {
                "target_duration": duration,
                "actual_duration": duration,
                "video_quality": video_quality,
                "voice_used": voice,
                "style": style_preference,
                "bgm_included": bool(bgm_path),
                "bgm_method": "Riffusion" if (bgm_path and RIFFUSION_AVAILABLE) else "Enhanced Musical" if bgm_path else "None",
                "enhanced_optimization": True,  # 🆕 개선된 최적화 적용
                "brand_validation": True,  # 🆕 브랜드 검증 적용
                "file_size_mb": round(file_size, 1),
                "generation_time": datetime.now().isoformat(),
                "optimized_prompt": optimized_prompt,
                "video_extension_applied": True,
                "workflow_version": "30sec_complete_v3.1"  # 🆕 버전 업데이트
            }
        }
        
        tasks_storage[task_id].update(
            status="completed",
            progress=100,
            current_step="완료",
            result=result,
            completed_at=datetime.now().isoformat()
        )
        
        print(f"✅ 30초 완성 광고 생성 완료: {task_id}")
        print(f"📁 최종 파일: {final_video_path} ({file_size:.1f}MB)")
        print(f"🎬 원본 5초 → {duration}초 완성 광고 변환 성공!")
        print(f"🎵 BGM 방식: {'Riffusion' if (bgm_path and RIFFUSION_AVAILABLE) else '향상된 음악적 BGM' if bgm_path else '없음'}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        tasks_storage[task_id].update(
            status="failed",
            error=str(e),
            current_step="실패",
            error_details=error_details[:1000]
        )
        print(f"❌ 30초 완성 광고 생성 실패: {task_id} - {e}")

def generate_quality_report(validated_audio: List[Dict[str, Any]]) -> Dict[str, Any]:
    """생성된 음성 파일들의 품질 검증 결과를 종합하여 리포트를 생성합니다."""
    if validated_audio is None:
        return {
            "error": "음성 데이터가 None입니다.",
            "summary": {
                "total_files": 0, "successful_files": 0, "failed_files": 0,
                "validation_rate": 0, "quality_pass_rate": 0, "average_quality_score": 0
            },
            "generated_at": datetime.now().isoformat()
        }
    
    if not validated_audio:
        return {
            "error": "검증할 음성 데이터가 없습니다.",
            "summary": {
                "total_files": 0, "successful_files": 0, "failed_files": 0,
                "validation_rate": 0, "quality_pass_rate": 0, "average_quality_score": 0
            },
            "generated_at": datetime.now().isoformat()
        }
    
    total_files = len(validated_audio)
    successful_files = len([audio for audio in validated_audio if audio is not None and audio.get("file")])
    failed_files = total_files - successful_files
    
    validated_files = [
        audio for audio in validated_audio 
        if audio is not None and audio.get("quality_validation", {}).get("available")
    ]
    passed_files = [
        audio for audio in validated_files 
        if audio is not None and audio.get("quality_validation", {}).get("passed")
    ]
    
    validation_rate = len(validated_files) / total_files if total_files > 0 else 0
    pass_rate = len(passed_files) / len(validated_files) if validated_files else 0
    
    quality_scores = []
    for audio in validated_files:
        if audio is not None:
            score = audio.get("quality_validation", {}).get("overall_score")
            if score is not None and isinstance(score, (int, float)):
                quality_scores.append(score)
    
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    return {
        "summary": {
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "validation_rate": round(validation_rate * 100, 1),
            "quality_pass_rate": round(pass_rate * 100, 1),
            "average_quality_score": round(avg_quality_score, 3)
        },
        "generated_at": datetime.now().isoformat()
    }

# ─────────────────────────────────────────────
# 8) 광고 생성 요청 및 상태/결과 조회 엔드포인트
# ─────────────────────────────────────────────

# 기존 광고 생성 엔드포인트 (하위 호환성)
@app.post("/api/v1/ads/generate", response_model=TaskResponse)
async def generate_advertisement(request: AdGenerationRequest, background_tasks: BackgroundTasks):
    """기존 광고 생성 (이미지 + 음성 + 비디오)"""
    if not request.brand or not request.keywords:
        raise HTTPException(status_code=400, detail="브랜드명과 키워드는 필수 입력 항목입니다.")

    task_id = str(uuid.uuid4())
    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "current_step": "대기 중...",
        "created_at": datetime.now().isoformat(),
        "request_data": request.dict()
    }
    
    background_tasks.add_task(process_ad_generation, task_id, request.dict())

    return TaskResponse(task_id=task_id, status="queued", message=f"광고 생성 작업이 시작되었습니다. 작업 ID: {task_id}")

# 🚀 새로운 30초 완성 광고 생성 엔드포인트 (개선 버전)
@app.post("/api/v1/ads/create-complete", response_model=TaskResponse)
async def create_complete_advertisement(request: CompleteAdRequest, background_tasks: BackgroundTasks):
    """🎉 30초 완성 광고 영상 생성 v3.1 (향상된 BGM + 브랜드 최적화)"""
    
    if not request.brand or not request.keywords:
        raise HTTPException(status_code=400, detail="브랜드명과 키워드는 필수입니다.")
    
    missing_services = []
    if not os.getenv("OPENAI_API_KEY"):
        missing_services.append("OpenAI API (TTS용)")
    if not COGVIDEO_AVAILABLE:
        missing_services.append("CogVideoX")
    if not check_ffmpeg_availability():
        missing_services.append("FFmpeg (영상 처리용)")
    
    if missing_services:
        raise HTTPException(
            status_code=400, 
            detail=f"필수 서비스가 설치되지 않았습니다: {', '.join(missing_services)}"
        )

    task_id = str(uuid.uuid4())
    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "current_step": "대기 중...",
        "created_at": datetime.now().isoformat(),
        "request_data": request.dict()
    }
    
    background_tasks.add_task(process_complete_ad_generation, task_id, request.dict())
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message=f"🎬 '{request.brand}' 브랜드 30초 완성 광고 생성이 시작되었습니다! (v3.1 향상된 BGM + 브랜드 최적화) 작업 ID: {task_id}"
    )

@app.get("/api/v1/ads/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="요청된 작업을 찾을 수 없습니다.")
    return TaskStatusResponse(**tasks_storage[task_id])

@app.get("/api/v1/ads/result/{task_id}")
async def get_task_result(task_id: str):
    """작업 결과 조회"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="요청된 작업을 찾을 수 없습니다.")
    task = tasks_storage[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"작업이 아직 완료되지 않았습니다. 현재 상태: {task['status']}")
    
    return {
        "task_id": task_id,
        "status": "completed",
        "result": task["result"],
        "metadata": {
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
            "request_data": task["request_data"]
        }
    }

# ─────────────────────────────────────────────
# 9) 작업 목록 조회 엔드포인트
# ─────────────────────────────────────────────
@app.get("/api/v1/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """작업 목록 조회"""
    all_tasks = list(tasks_storage.values())
    sorted_tasks = sorted(all_tasks, key=lambda x: x["created_at"], reverse=True)
    return {"tasks": sorted_tasks[offset:offset+limit], "total": len(all_tasks), "limit": limit, "offset": offset}

# ─────────────────────────────────────────────
# 10) 다운로드 엔드포인트
# ─────────────────────────────────────────────
@app.get("/download/{task_id}")
async def download_final_video(task_id: str):
    """최종 광고 영상 다운로드"""
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    task = tasks_storage[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="작업이 완료되지 않았습니다.")
    
    # 완전 통합 광고의 경우
    if "final_video" in task["result"]["content"]:
        final_video = task["result"]["content"]["final_video"]
        if not os.path.exists(final_video):
            raise HTTPException(status_code=404, detail="영상 파일을 찾을 수 없습니다.")
        
        filename = f"{task['request_data']['brand']}_30sec_ad_{task_id[:8]}.mp4"
        return FileResponse(
            final_video,
            media_type="video/mp4",
            filename=filename
        )
    
    # 기존 광고의 경우 (첫 번째 비디오 반환)
    elif "videos" in task["result"]["content"] and task["result"]["content"]["videos"]:
        video_path = task["result"]["content"]["videos"][0]
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="영상 파일을 찾을 수 없습니다.")
        
        filename = f"{task['request_data']['brand']}_ad_{task_id[:8]}.mp4"
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=filename
        )
    
    else:
        raise HTTPException(status_code=404, detail="다운로드 가능한 영상 파일이 없습니다.")

# 🆕 [새로 추가] 브랜드 프리셋 조회 엔드포인트
@app.get("/api/v1/brands/presets")
async def get_brand_presets():
    """지원하는 브랜드 프리셋 목록 조회"""
    return {
        "supported_brands": list(BRAND_PRESETS.keys()),
        "presets": BRAND_PRESETS,
        "total_brands": len(BRAND_PRESETS),
        "message": "브랜드별 최적화된 프리셋을 제공합니다."
    }

# 🆕 [새로 추가] BGM 스타일 조회 엔드포인트
@app.get("/api/v1/bgm/styles")
async def get_bgm_styles():
    """지원하는 BGM 스타일 목록 조회"""
    return {
        "supported_styles": ["모던하고 깔끔한", "따뜻하고 아늑한", "미니멀하고 프리미엄한", "역동적이고 에너지", "감성적이고 로맨틱"],
        "enhanced_musical_bgm": check_ffmpeg_availability(),
        "riffusion_available": RIFFUSION_AVAILABLE,
        "features": {
            "chord_progressions": True,
            "rhythm_patterns": True,
            "style_specific_harmonies": True,
            "fallback_system": True
        },
        "message": "화음 기반 향상된 BGM 생성을 지원합니다."
    }

# 글로벌 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """API 요청 처리 중 발생하는 모든 예외를 캐치하여 500 Internal Server Error 응답을 반환합니다."""
    print(f"💥 서버 에러 발생: {exc}")
    import traceback
    print(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": f"서버 내부 오류가 발생했습니다: {exc}"})

# ─────────────────────────────────────────────
# 11) 서버 실행
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🚀 AI 30초 완성 광고 크리에이터 서버 v3.1을 시작합니다...")
    print("🎯 NEW: 향상된 음악적 BGM + 브랜드별 최적화!")
    print("🎵 특징: 화음 기반 BGM, CogVideoX 프롬프트 최적화, 브랜드 검증")
    print("📋 엔드포인트:")
    print("    - GET    /                        : 웹 인터페이스")
    print("    - POST   /api/v1/ads/create-complete : 🆕 30초 완성 광고 생성 v3.1")
    print("    - POST   /api/v1/ads/generate    : 기존 광고 생성")
    print("    - GET    /api/v1/brands/presets  : 🆕 브랜드 프리셋 조회")
    print("    - GET    /api/v1/bgm/styles      : 🆕 BGM 스타일 조회")
    print("    - GET    /docs                   : API 문서")
    print("    - GET    /download/{task_id}     : 완성된 30초 영상 다운로드")
    print("🎬 v3.1 개선사항: 화음진행 BGM, 엔디비아 최적화, 품질검증 강화")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)