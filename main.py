# main.py — AI 광고 크리에이터 FastAPI 서버 (CogVideoX-2b + TTS + BGM 통합)

# ─────────────────────────────────────────────
# 1) 환경 변수 로드 및 초기 설정, 필수 라이브러리 임포트
# ─────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv() # .env 파일 로드: 환경변수 (API 키 등) 불러옴.

# PyTorch CUDA 메모리 관리 설정: GPU 메모리 단편화 방지, 대용량 모델 로드 시 유리.
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
print("✅ DEBUG: PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True 환경 변수가 설정되었습니다.")

# OpenAI API Key 로드 확인: 디버깅용, 키가 제대로 설정됐는지 즉시 체크.
_debug_api_key = os.getenv("OPENAI_API_KEY")
if _debug_api_key:
    print(f"✅ DEBUG: OpenAI API Key가 환경 변수에서 성공적으로 로드되었습니다!")
    print(f"DEBUG: 키 시작 부분: {_debug_api_key[:5]}...")
else:
    print(f"❌ DEBUG: OpenAI API Key가 환경 변수에서 로드되지 않았습니다.")

# 표준 라이브러리 임포트: Python 기본 기능 모듈들.
import sys # 시스템 관련 기능 (경로 조작 등)
import uuid # 고유 ID 생성 (작업 ID에 활용)
import asyncio # 비동기 처리 지원
import subprocess # 외부 프로그램 실행 (FFmpeg 등)
import json # JSON 데이터 처리
import math # 수학 함수 (나눗셈 올림 등)
import time # 시간 관련 (지연 등)
import shutil # 파일/디렉토리 복사/삭제

from pathlib import Path # 파일 시스템 경로 객체 지향적 처리
from datetime import datetime # 날짜/시간 처리
from typing import Dict, Any, Optional, List, Literal # 타입 힌트 (코드 가독성/오류 방지)

# 서드파티 라이브러리 임포트: FastAPI, Pydantic 등 외부 설치 필요 모듈.
from pydantic import BaseModel, Field # 데이터 유효성 검사, API 요청/응답 모델 정의

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request # 웹 API 프레임워크 핵심, 예외, 백그라운드 작업, 요청 객체
from fastapi.middleware.cors import CORSMiddleware # CORS (교차 출처 자원 공유) 설정
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse # API 응답 타입
from fastapi.templating import Jinja2Templates # HTML 템플릿 렌더링

# 로컬 애플리케이션 모듈 임포트: 프로젝트 내부의 사용자 정의 모듈.
current_dir = Path(__file__).parent.absolute() # 현재 파일(main.py)의 절대 경로
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir)) # 현재 디렉토리를 Python 검색 경로에 추가
if str(current_dir / "app") not in sys.path:
    sys.path.insert(0, str(current_dir / "app")) # 'app' 서브디렉토리를 Python 검색 경로에 추가 (모듈 임포트 위함)

# CogVideoX-2b 유틸리티 임포트 및 가용성 플래그 설정: T2V 모델 관련 모듈 로드, 성공 여부 플래그 세팅.
try:
    import app.utils.CogVideoX_2b_utils as cog_utils # 모듈 자체를 임포트하고 별칭 부여
    
    # 이제 CogVideoXGenerator, check_cogvideox_installation 등은 cog_utils. 로 접근합니다.
    # COGVIDEODX_AVAILABLE 등의 플래그는 cog_utils 모듈 내부에 정의된 것을 사용합니다.
    COGVIDEODX_AVAILABLE = cog_utils.COGVIDEODX_AVAILABLE # CogVideoX-2b 모델 사용 가능 여부 플래그
    BGM_GENERATION_AVAILABLE = cog_utils.BGM_GENERATION_AVAILABLE # BGM 생성 가능 여부 플래그
    RIFFUSION_PIPELINE_AVAILABLE = cog_utils.RIFFUSION_PIPELINE_AVAILABLE # Riffusion 파이프라인 사용 가능 여부 플래그
    
    print("✅ CogVideoX-2b utils 모듈 로드 성공")
except ImportError as e:
    # 모듈 로드 실패 시 관련 기능 모두 비활성화 및 안내 메시지 출력.
    COGVIDEODX_AVAILABLE = False # CogVideoX-2b 기능 비활성화
    BGM_GENERATION_AVAILABLE = False # BGM 생성 기능 비활성화
    RIFFUSION_PIPELINE_AVAILABLE = False # Riffusion 파이프라인 비활성화
    print(f"❌ CogVideoX-2b utils 모듈 로드 실패: {e}")
    print("📌 CogVideoX-2b 기능 없이 기본 이미지+오디오 합성 모드로 실행됩니다.")

# Riffusion BGM 기능 최종 가용성 플래그: Riffusion 파이프라인과 BGM 생성이 모두 가능할 때 활성화.
RIFFUSION_AVAILABLE = RIFFUSION_PIPELINE_AVAILABLE and BGM_GENERATION_AVAILABLE # Riffusion BGM 최종 가용성
if RIFFUSION_AVAILABLE:
    print("✅ Riffusion BGM 기능이 활성화되었습니다.")
else:
    print("⚠️ Riffusion BGM 기능은 비활성화되었습니다. FFmpeg 기반 향상된 BGM을 사용합니다.")

# ─────────────────────────────────────────────
# 2) FastAPI 애플리케이션 초기화 (모든 라우트/핸들러 함수보다 먼저 정의되어야 함)
# ─────────────────────────────────────────────
app = FastAPI(
    title="🎬 AI Complete Advertisement Creator API", # API 문서 제목
    description="AI 기반 멀티모달 광고 콘텐츠 생성 및 품질 검증 시스템 (CogVideoX-2b + TTS + BGM)", # API 설명
    version="3.3.0", # API 버전
    docs_url="/docs", # Swagger UI 문서 경로
    redoc_url="/redoc", # ReDoc 문서 경로
    swagger_ui_favicon_url="/favicon.ico", # Swagger UI 파비콘
    redoc_favicon_url="/favicon.ico" # ReDoc 파비콘
)

# Jinja2 템플릿 디렉토리 설정: 웹 페이지 렌더링에 사용될 HTML 파일 위치 지정.
templates = Jinja2Templates(directory="templates") # HTML 템플릿 로드 경로 설정

# CORS 설정: 웹 브라우저에서 다른 도메인으로부터의 API 요청을 허용하기 위함.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 모든 출처 허용 (개발용, 실제 운영에서는 특정 도메인만 허용 권장)
    allow_credentials=True, # 자격 증명(쿠키, HTTP 인증 등) 허용
    allow_methods=["*"], # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"], # 모든 HTTP 헤더 허용
)

# ─────────────────────────────────────────────
# 3) 전역 상태 및 지연 초기화 워크플로우 정의
# ─────────────────────────────────────────────

# tasks_storage 업데이트 함수: 작업 상태(진행률, 현재 단계 등)를 안전하게 업데이트하고 콘솔에 출력.
def update_task_status(task_id: str, **kwargs):
    """안전한 task 상태 업데이트"""
    if task_id in tasks_storage:
        tasks_storage[task_id].update(kwargs) # 작업 상태 정보 업데이트
        print(f"📊 Task {task_id[:8]}: {kwargs.get('current_step', 'Unknown')} ({kwargs.get('progress', 0)}%)") # 콘솔에 진행 상황 출력

# 비동기 작업 저장소: 현재 진행 중인 작업들의 상태와 결과를 저장하는 딕셔너리.
tasks_storage: Dict[str, Dict[str, Any]] = {} # 작업 ID를 키로, 작업 상태 딕셔너리를 값으로 저장

# AI 워크플로우 지연 초기화 관련 변수: 필요할 때까지 AI 모델 로딩을 미룸.
ai_workflow = None # AI 워크플로우 인스턴스
WORKFLOW_AVAILABLE = False # AI 워크플로우 사용 가능 여부 플래그

# AI 워크플로우 초기화 함수: AdCreatorWorkflow 클래스를 로드하고 인스턴스화.
def initialize_workflow():
    """AI 워크플로우 지연 초기화"""
    global ai_workflow, WORKFLOW_AVAILABLE # 전역 변수 ai_workflow, WORKFLOW_AVAILABLE 사용 선언
    if ai_workflow is None: # 아직 초기화되지 않았다면
        try:
            print("🔄 AI 워크플로우 지연 초기화 시작...")
            from app.agents.workflow import AdCreatorWorkflow # 워크플로우 클래스 임포트
            api_key = os.getenv("OPENAI_API_KEY") # OpenAI API 키 로드
            if api_key:
                print(f"✅ 워크플로우 초기화용 API Key 확인: {api_key[:5]}...")
                ai_workflow = AdCreatorWorkflow() # API 키로 워크플로우 초기화 (여기서는 키를 직접 전달하진 않음)
            else:
                print("❌ 워크플로우 초기화용 API Key를 찾을 수 없음")
                ai_workflow = AdCreatorWorkflow() # 키 없어도 일단 초기화 시도
            WORKFLOW_AVAILABLE = True # 워크플로우 사용 가능 플래그 True
            print("✅ AI 워크플로우 초기화 완료")
        except ImportError as e:
            # 워크플로우 모듈 임포트 실패 시.
            print(f"⚠️ AI 워크플로우 import 실패: {e}")
            WORKFLOW_AVAILABLE = False # 워크플로우 사용 불가
            ai_workflow = None # 인스턴스 초기화 실패

# OpenAI 비동기 클라이언트 싱글톤: OpenAI API 호출에 사용할 클라이언트 객체를 한 번만 생성.
_openai_client = None # 클라이언트 객체를 저장할 변수 (초기값 None)

async def get_openai_client(): # 비동기 함수로 정의
    """OpenAI 비동기 클라이언트 싱글톤"""
    global _openai_client # 전역 변수 _openai_client 사용 선언
    if _openai_client is None: # 아직 클라이언트가 생성되지 않았다면
        import openai # openai 라이브러리 임포트
        api_key = os.getenv("OPENAI_API_KEY") # 환경 변수에서 API 키 로드
        if not api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.") # 키 없으면 에러 발생
        _openai_client = openai.AsyncOpenAI(api_key=api_key) # AsyncOpenAI로 비동기 클라이언트 생성
    return _openai_client # 생성된(또는 기존) 클라이언트 반환

# ─────────────────────────────────────────────
# 🎯 개선된 프롬프트 템플릿 및 유틸리티 함수들 (여기는 변하지 않습니다)
# ─────────────────────────────────────────────

PROMPT_TEMPLATE = """
You are an expert ad copywriter specializing in short-form video advertisements.
Generate a JSON-formatted advertisement with three scenes for {brand}.
Use these keywords: {keywords}.
The campaign type is {campaign_type} and the style preference is {style_preference}.

IMPORTANT REQUIREMENTS:
1. First scene MUST show {brand} product clearly within first 3 seconds
2. Each scene should be concise and product-focused
3. Visual descriptions must be clear and specific for AI video generation
4. Include brand name and product in narration early
5. Focus on core product benefits and brand identity

Return valid JSON in this exact format:
{
  "scenes": [
    {
      "name": "Scene name",
      "duration": "time in seconds",
      "description": "visual description (in English, product-focused, specific)",
      "narration": "voice-over text (Korean, brand name first)"
    }
  ]
}

Brand-specific optimization examples:
- Apple iPhone: "iPhone held in hands, premium metal design, iOS interface, Apple logo visible"
- Nike shoes: "Nike running shoes closeup, athlete wearing them, swoosh logo prominent"
- Samsung Galaxy: "Samsung Galaxy phone displayed, advanced features demo, Samsung branding"
- Starbucks: "Starbucks coffee cup prominent, barista making drink, logo visible"
""" # 스토리보드 생성을 위한 일반 프롬프트 템플릿.

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

Brand-specific optimization examples:
- Apple iPhone: "iPhone in hands from first frame, premium design closeup, iOS interface interaction, Apple logo prominent"
- Nike shoes: "Nike running shoes closeup, athlete foot movement, swoosh logo prominent"
- Samsung Galaxy: "Samsung Galaxy phone center frame, advanced tech features demo, Samsung branding"
- Starbucks: "Starbucks coffee cup prominent, barista making drink, logo visible"
""" # 단일 통합 광고 컨셉 (나레이션 + 영상 설명) 생성을 위한 프롬프트.

def optimize_zeroscope_prompt_enhanced(brand, visual_description, keywords, style_preference):
    """CogVideoX-2b용 비디오 프롬프트 최적화: 브랜드 및 키워드 기반으로 상세 프롬프트 생성."""
    def create_brand_scenario(brand_name):
        brand_lower = brand_name.lower()
        # 특정 브랜드 키워드에 따라 제품 타입, 주요 시각, 브랜드 요소, 제품 동작, 필수 요소 등을 상세 정의.
        # AI 모델이 이해하기 쉽도록 구체적인 시나리오 힌트 제공.
        if any(keyword in brand_lower for keyword in ['phone', 'smartphone', 'galaxy', 'iphone', 'apple', '애플', '삼성', 'samsung']):
            product_type = "smartphone device"
            primary_visual = f"{brand_name} smartphone prominently displayed in center frame from first second"
            brand_elements = f"{brand_name} logo clearly visible on device, modern smartphone design"
            product_actions = "hands holding smartphone, finger touching screen, device interaction"
        elif any(keyword in brand_lower for keyword in ['shoe', 'shoes', 'sneaker', 'nike', '나이키', 'adidas', 'puma']):
            product_type = "footwear"
            primary_visual = f"{brand_name} shoes closeup shot from first frame center"
            brand_elements = f"{brand_name} logo prominently visible, athletic footwear design"
            product_actions = "person wearing shoes, walking or running motion, shoe details"
        elif any(keyword in brand_lower for keyword in ['coffee', 'cafe', 'starbucks', '스타벅스', '커피']):
            product_type = "beverage"
            primary_visual = f"{brand_name} coffee cup with logo prominently displayed from first frame"
            brand_elements = f"{brand_name} logo clearly visible on cup, cafe environment"
            product_actions = "barista making coffee, steam rising, customer holding cup"
        elif any(keyword in brand_lower for keyword in ['car', 'auto', 'bmw', 'toyota', 'tesla', '자동차', '현대', 'hyundai']):
            product_type = "automotive"
            primary_visual = f"{brand_name} vehicle prominently displayed from first frame"
            brand_elements = f"{brand_name} logo clearly visible on vehicle, sleek car design"
            product_actions = "car driving, interior features, vehicle exterior showcase"
        elif any(keyword in brand_lower for word in ['graphics', 'gpu', 'nvidia', '엔디비아', 'rtx', 'gaming']):
            product_type = "technology"
            primary_visual = f"{brand_name} graphics card prominently displayed from first frame"
            brand_elements = f"{brand_name} logo clearly visible, high-tech gaming setup"
            product_actions = "graphics card installation, gaming performance, RGB lighting"
        elif any(keyword in brand_lower for word in ['food', 'restaurant', 'mcdonald', '맥도날드', 'kfc', 'burger']):
            product_type = "food"
            primary_visual = f"{brand_name} food product prominently displayed from first frame"
            brand_elements = f"{brand_name} logo clearly visible, appetizing food presentation"
            product_actions = "food preparation, eating scene, product showcase"
        elif any(keyword in brand_lower for word in ['cosmetic', 'beauty', 'makeup', 'skincare', '화장품', '뷰티']):
            product_type = "beauty"
            primary_visual = f"{brand_name} beauty product prominently displayed from first frame"
            brand_elements = f"{brand_name} logo clearly visible on packaging, elegant product design"
            product_actions = "product application, beauty routine, skincare demonstration"
        else:
            product_type = "product"
            primary_visual = f"{brand_name} product prominently displayed in center frame from first second"
            brand_elements = f"{brand_name} logo clearly visible, professional product presentation"
            product_actions = f"person using {brand_name} product, product demonstration, feature showcase"
        return {
            "product_type": product_type,
            "primary_visual": primary_visual,
            "brand_elements": brand_elements,
            "product_actions": product_actions,
            "brand_keywords": f"{brand_name} {product_type} logo branding",
            "mandatory_elements": f"{brand_name} logo and product must be clearly visible from first frame"
        }

    brand_info = create_brand_scenario(brand) # 브랜드 시나리오 생성
    style_cinematography = { # 영상 스타일별 시각적 힌트 매핑
        "모던하고 깔끔한": "clean modern commercial style, professional lighting, minimal background, sharp focus",
        "따뜻하고 아늑한": "warm golden lighting, cozy atmosphere, soft focus, comfortable setting",
        "미니멀하고 프리미엄한": "luxury premium style, elegant lighting, sophisticated clean background",
        "역동적이고 에너지": "dynamic energetic movement, vibrant colors, active lifestyle, motion blur",
        "감성적이고 로맨틱": "emotional cinematic style, romantic lighting, heartwarming atmosphere",
        "전문적이고 신뢰": "professional corporate style, trustworthy presentation, business environment"
    }
    style_tech = style_cinematography.get(style_preference, style_cinematography["모던하고 깔끔한"]) # 선택 스타일 없으면 기본값 적용
    keywords_lower = keywords.lower() # 키워드 소문자 변환
    keyword_enhancements = [] # 추가 키워드 리스트
    # 특정 키워드에 따라 추가적인 시각적 설명 덧붙임
    if any(word in keywords_lower for word in ['premium', 'luxury', '프리미엄', '고급']):
        keyword_enhancements.append("luxury premium quality")
    if any(word in keywords_lower for word in ['new', 'latest', '신제품', '최신']):
        keyword_enhancements.append("latest new product launch")
    if any(word in keywords_lower for word in ['technology', 'tech', '기술', '첨단']):
        keyword_enhancements.append("advanced technology innovation")
    if any(word in keywords_lower for word in ['performance', '성능', 'power']):
        keyword_enhancements.append("high performance powerful")

    core_elements = [ # 핵심 프롬프트 요소들 조합
        brand_info['primary_visual'], # 주요 시각적 요소 (브랜드/제품)
        brand_info['brand_elements'], # 브랜드 로고 등 시각적 요소
        brand_info['product_actions'], # 제품 사용/작동 모습
        visual_description, # AI가 생성한 상세 비주얼 설명
        brand_info['brand_keywords'], # 브랜드 관련 추가 키워드
        style_tech, # 영상 스타일
        "commercial advertisement style", # 상업 광고 스타일
        brand_info['mandatory_elements'], # 필수 포함 요소 (첫 프레임 제품 등)
        "professional cinematography, high quality video, brand focused" # 영상 품질/포커스
    ]
    
    if keyword_enhancements:
        core_elements.extend(keyword_enhancements) # 추가 키워드 있으면 포함
    optimized_prompt = ", ".join(core_elements) # 모든 요소를 콤마로 연결하여 최종 프롬프트 생성
    if len(optimized_prompt) > 450: # 프롬프트 길이가 너무 길면 핵심 요소만 남김
        essential_elements = [
            brand_info['primary_visual'],
            brand_info['brand_elements'],
            brand_info['brand_keywords'],
            style_tech,
            "commercial advertisement",
            brand_info['mandatory_elements']
        ]
        optimized_prompt = ", ".join(essential_elements)
    print(f"🎯 범용 브랜드 ({brand}) 최적화 프롬프트 생성: {optimized_prompt}")
    return optimized_prompt # 최적화된 비디오 생성 프롬프트 반환

def validate_brand_prompt(brand, prompt):
    """생성된 비디오 프롬프트에 브랜드 필수 요소(이름, 로고, 제품)가 포함됐는지 검증 및 강화."""
    brand_lower = brand.lower()
    prompt_lower = prompt.lower()
    enhancements = [] # 추가할 강화 요소 리스트
    if brand_lower not in prompt_lower:
        enhancements.append(f"{brand} prominently displayed") # 브랜드명 없으면 추가
    if "logo" not in prompt_lower:
        enhancements.append(f"{brand} logo clearly visible") # 로고 없으면 추가
    if "product" not in prompt_lower and brand_lower not in prompt_lower:
        enhancements.append(f"{brand} product central") # 제품 키워드 없으면 추가
    if enhancements:
        enhanced_prompt = f"{', '.join(enhancements)}, {prompt}" # 강화 요소와 기존 프롬프트 결합
        print(f"🔧 브랜드 ({brand}) 프롬프트 강화: {enhancements}")
        return enhanced_prompt # 강화된 프롬프트 반환
    return prompt # 강화할 필요 없으면 원본 반환

# 브랜드별 빠른 예시 프리셋: UI/사용자 편의를 위해 미리 정의된 브랜드별 키워드, 스타일, 시각적 초점.
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

# 이미지+오디오 합성 함수: T2V 모델(CogVideoX) 실패 시 폴백으로 사용. FFmpeg 활용.
def generate_video_from_image_and_audio(image_path: str, audio_path: str, output_dir: str):
    """이미지 파일과 오디오 파일 결합해 MP4 비디오 생성 (FFmpeg 사용)"""
    try:
        os.makedirs(output_dir, exist_ok=True) # 출력 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 타임스탬프 생성
        output_path = os.path.join(output_dir, f"ad_scene_{timestamp}.mp4") # 출력 파일 경로

        # 입력 파일 존재 여부 확인: 없으면 에러 발생
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        # 오디오 길이 확인: FFprobe로 오디오 파일 길이 측정, 실패 시 기본 10초
        try:
            probe_command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
            result = subprocess.run(probe_command, capture_output=True, text=True, check=True, timeout=30)
            audio_duration = float(result.stdout.strip())
        except Exception:
            audio_duration = 10 # 오디오 길이 측정 실패 시 기본값
            print(f"⚠️ 오디오 길이 확인 실패. 기본값 {audio_duration}초로 설정합니다.")

        command = [ # FFmpeg 명령 구성: 이미지 반복, 오디오 결합, 비디오 인코딩.
            "ffmpeg",
            "-loop", "1", # 이미지를 루프 (반복)
            "-i", image_path, # 입력 이미지 파일
            "-i", audio_path, # 입력 오디오 파일
            "-c:v", "libx264", # 비디오 코덱 설정
            "-tune", "stillimage", # 스틸 이미지에 최적화된 튜닝
            "-c:a", "aac", # 오디오 코덱 설정
            "-b:a", "192k", # 오디오 비트레이트
            "-pix_fmt", "yuv420p", # 픽셀 포맷 (호환성 위함)
            "-t", str(audio_duration), # 비디오 길이 (오디오 길이에 맞춤)
            "-shortest", # 가장 짧은 스트림에 맞춰 종료 (오디오/비디오 중 짧은 것 기준)
            "-y", # 덮어쓰기 허용
            "-vf", "scale=1024:1024", # 비디오 필터: 1024x1024로 스케일링
            output_path # 출력 파일 경로
        ]

        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300) # FFmpeg 실행 및 타임아웃 300초

        # 출력 파일 존재 여부 재확인
        if not os.path.exists(output_path):
            raise Exception("영상 파일이 생성되지 않았습니다.")
        
        print(f"✅ 영상 생성 성공 (이미지+오디오): {output_path}")
        return output_path # 생성된 비디오 파일 경로 반환
        
    except subprocess.TimeoutExpired: # FFmpeg 시간 초과 에러
        print("❌ 영상 생성 시간 초과")
        raise RuntimeError("영상 생성 시간 초과")
    except subprocess.CalledProcessError as e: # FFmpeg 실행 중 에러
        print(f"❌ 영상 생성 실패 (이미지+오디오): {e.stderr.decode()}")
        raise RuntimeError(f"FFmpeg 영상 생성 실패: {e.stderr.decode()}")
    except Exception as e: # 기타 예외 처리
        print(f"❌ 영상 생성 중 예외 발생: {e}")
        raise RuntimeError(f"영상 생성 실패: {e}")

# ─────────────────────────────────────────────
# 4) Pydantic 모델 정의
# ─────────────────────────────────────────────

class AdGenerationRequest(BaseModel): # 기존 광고 생성 요청 데이터 모델 (FastAPI Request Body 유효성 검사용)
    brand: str = Field(..., description="광고할 브랜드명", example="스타벅스")
    keywords: List[str] = Field(..., description="광고 내용에 포함될 키워드 리스트", example=["커피", "겨울", "따뜻함"])
    target_audience: str = Field(..., description="광고의 타겟 고객층", example="20-30대 직장인")
    campaign_type: str = Field(default="브랜드 인지도", description="광고 캠페인의 유형", example="브랜드 인지도")
    duration: int = Field(default=30, description="생성될 광고의 총 길이 (초 단위)", example=30, ge=15, le=120)

    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(
        default="alloy",
        description="텍스트-음성 변환(TTS)에 사용될 음성 모델 선택"
    )

    enable_quality_validation: bool = Field( # 음성 품질 검증 활성화 여부
        default=True,
        description="Whisper 모델 기반의 생성된 음성 품질 검증 활성화 여부"
    )
    min_quality_score: float = Field( # 최소 품질 점수 (0.0~1.0)
        default=0.8,
        description="음성이 '품질 기준 통과'로 간주될 최소 품질 점수 (0.0~1.0 사이)",
        ge=0.0,
        le=1.0
    )
    max_retry_attempts: int = Field( # 재시도 최대 횟수
        default=2,
        description="음성 품질 기준 미달 시 내레이션 재시도 최대 횟수",
        ge=0,
        le=5
    )

    enable_t2v: bool = Field( # Text-to-Video 기능 활성화 여부
        default=True,
        description="Text-to-Video (CogVideoX-2b) 생성 기능 활성화 여부"
    )

    class Config: # Pydantic 모델 설정
        json_schema_extra = { # API 문서(Swagger)에 표시될 예시 JSON
            "example": {
                "brand": "스타벅스",
                "keywords": ["커피", "겨울", "따뜻함", "신메뉴"],
                "target_audience": "20-30대 직장인",
                "campaign_type": "브랜드 인지도",
                "style_preference": "모던하고 깔림한",
                "duration": 30,
                "voice": "nova",
                "enable_quality_validation": True,
                "min_quality_score": 0.8,
                "max_retry_attempts": 2,
                "enable_t2v": True
            }
        }

class CompleteAdRequest(BaseModel): # 30초 완성 광고 생성 요청 데이터 모델 (FastAPI Request Body 유효성 검사용)
    brand: str = Field(..., description="브랜드명")
    keywords: str = Field(..., description="키워드 또는 문장 (자유 형식)")

    target_audience: str = Field(default="일반 소비자", description="타겟 고객층")
    style_preference: str = Field(default="모던하고 깔끔한", description="영상 스타일")
    
    duration: Literal[15, 30] = Field(default=30, description="영상 길이(초)", example=30) # 영상 길이 선택 (15초, 30초 중 하나)

    video_quality: Literal["fast", "balanced", "high"] = Field(default="balanced") # 비디오 품질
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(default="nova") # TTS 음성

    enable_bgm: bool = Field(default=True, description="BGM 생성 활성화") # BGM 생성 여부
    bgm_prompt: Optional[str] = Field(None, description="배경 음악 생성용 프롬프트 (비어있으면 키워드/브랜드 사용)", example="energetic electronic music for car ad") # BGM 프롬프트 (선택 사항)
    bgm_style: str = Field(default="auto", description="BGM 스타일") # BGM 스타일 (현재는 bgm_prompt가 우선)

    class Config: # Pydantic 모델 설정
        json_schema_extra = { # API 문서(Swagger)에 표시될 예시 JSON
            "example": {
                "brand": "엔디비아",
                "keywords": "RTX 그래픽카드, 게이밍 성능, AI 컴퓨팅",
                "target_audience": "게이머 및 크리에이터",
                "style_preference": "모던하고 깔끔한",
                "duration": 30,
                "video_quality": "balanced",
                "voice": "nova",
                "enable_bgm": True,
                "bgm_prompt": "futuristic gaming music",
            }
        }

class TaskResponse(BaseModel): # 작업 시작 시 응답 모델
    task_id: str # 생성된 작업 ID
    status: str # 작업 상태 (예: "queued")
    message: str # 사용자에게 보낼 메시지

class TaskStatusResponse(BaseModel): # 작업 상태 조회 시 응답 모델
    task_id: str # 작업 ID
    status: str # 현재 상태 (예: "processing", "completed", "failed")
    progress: int # 진행률 (0-100%)
    current_step: str # 현재 진행 중인 단계 설명
    estimated_completion: Optional[str] = None # 예상 완료 시간 (선택 사항)
    error: Optional[str] = None # 에러 메시지 (실패 시)

class QualityValidationSettings(BaseModel): # 품질 검증 설정 조회 응답 모델
    whisper_available: bool # Whisper 모델 사용 가능 여부
    supported_models: List[str] # 지원되는 Whisper 모델 목록
    default_settings: Dict[str, Any] # 기본 설정 값

# ─────────────────────────────────────────────
# 5) API 엔드포인트 정의 (루트 및 헬스 체크)
# ─────────────────────────────────────────────

@app.get("/favicon.ico", include_in_schema=False) # 파비콘 제공 엔드포인트
async def favicon():
    """서버 루트에 위치한 favicon.ico 파일 반환."""
    return FileResponse(Path(__file__).parent / "favicon.ico")

@app.get("/", response_class=HTMLResponse) # 루트 경로 (`/`) 접속 시 웹 인터페이스 제공
async def serve_frontend(request: Request):
    """메인 웹 인터페이스 제공 (templates/complete_ad_creator.html 렌더링)."""
    try:
        return templates.TemplateResponse("complete_ad_creator.html", {"request": request}) # HTML 템플릿 렌더링
    except Exception: # 템플릿 로드 실패 시 대체 HTML 응답
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 광고 크리에이터 v3.3.0</title> <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .info { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .api-link { display: block; text-align: center; background: #667eea; color: white; padding: 15px; border-radius: 10px; text-decoration: none; margin: 10px 0; }
        .api-link:hover { background: #5a6fd8; }
        .feature { color: #28a745; font-weight: bold; }
        .new-feature { color: #dc3545; font-weight: bold; }
        .improved { color: #fd7e14; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 광고 크리에이터 v3.3.0</h1> <div class="info">
            <h3>📋 사용 가능한 기능</h3>
            <ul>
                <li>✅ CogVideoX-2b AI 영상 생성 (주력 모델)</li> <li>✅ OpenAI TTS 나레이션</li>
                <li class="new-feature">🆕 향상된 음악적 BGM 생성</li>
                <li class="new-feature">🆕 브랜드별 최적화 프롬프트</li>
                <li class="improved">🔧 안정성 개선 (파일 검증, 타임아웃 추가)</li>
                <li class="feature">🎵 화음 기반 BGM 자동 생성</li>
                <li class="feature">🎬 30초 완성 광고 자동 생성 (짧은 클립 합성 필요)</li> <li>✅ FFmpeg 영상 합성</li>
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
            <h3>🎯 v3.3.0 개선사항</h3> <p>• <span class="new-feature">🚀 CogVideoX-2b 주력 모델 전환</span> - 더 안정적인 T2V (짧은 클립 생성)</p> <p>• <span class="improved">🔧 안정성 강화</span> - 파일 존재 확인, 타임아웃 추가</p>
            <p>• <span class="improved">🔧 에러 핸들링 개선</span> - 더 상세한 오류 메시지</p>
            <p>• <span class="improved">🔧 메모리 최적화</span> - OpenAI 클라이언트 싱글톤</p>
            <p>• <span class="new-feature">🎵 화음 기반 음악적 BGM</span> - 코드 진행과 리듬 패턴</p>
            <p>• <span class="feature">⚡ 폴백 시스템</span> - 안정성 향상</p>
        </div>
    </div>
</body>
</html>
        """, status_code=200)

def get_available_whisper_models():
    """Whisper 모델 목록 동적 조회: 시스템에 설치된 Whisper 모델 종류 반환."""
    try:
        import whisper
        available = whisper.available_models() # 사용 가능한 Whisper 모델 목록 조회
        return sorted(list(available)) # 정렬하여 반환
    except ImportError: # Whisper 모듈이 없으면
        return [] # 빈 리스트 반환
    except Exception as e: # 기타 에러 발생 시
        print(f"Warning: whisper.available_models() 조회 오류: {e}") # 경고 출력
        return ["tiny", "base", "small", "medium", "large"] # 기본 모델 목록 반환

def check_ffmpeg_availability():
    """FFmpeg 설치 여부 확인: 시스템 PATH에 FFmpeg 있는지 체크."""
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                                 capture_output=True, text=True, check=True, timeout=10) # FFmpeg 버전 명령어 실행
        return result.returncode == 0 # 성공적으로 실행되면 True 반환
    except Exception: # 에러 발생 시
        return False # False 반환

@app.get("/health") # 헬스 체크 엔드포인트: API 서버 및 주요 서비스 상태 반환.
async def health_check():
    """API 서버의 전반적인 상태 확인"""
    
    whisper_available = False # Whisper 모델 가용성 초기화
    whisper_error = None # Whisper 오류 메시지 초기화
    supported_models = [] # 지원 모델 목록 초기화
    
    try: # Whisper 가용성 체크
        import whisper
        whisper_available = True
        supported_models = get_available_whisper_models() # 사용 가능한 Whisper 모델 목록 가져오기
    except Exception as e:
        whisper_error = str(e) # 오류 메시지 저장
        supported_models = [] # 목록 비우기
    
    librosa_available = False # Librosa 가용성 초기화
    try: # Librosa 가용성 체크 (오디오 분석용)
        import librosa
        librosa_available = True
    except Exception:
        pass # 오류 발생 시 아무것도 하지 않음
    
    ffmpeg_available = check_ffmpeg_availability() # FFmpeg 가용성 체크
    
    return { # 서버 상태를 JSON 응답으로 반환
        "status": "healthy", # 서버 상태
        "version": "3.3.0", # API 버전
        "timestamp": datetime.now().isoformat(), # 현재 시간
        "services": { # 각 서비스별 상태
            "api": "running", # API 서버 실행 상태
            "ai_workflow": "ready" if WORKFLOW_AVAILABLE else "unavailable", # AI 워크플로우 상태
            "task_storage": "ready", # 작업 저장소 상태
            "openai_api": "ready" if os.getenv("OPENAI_API_KEY") else "no_api_key", # OpenAI API 키 여부
            "whisper_quality_validation": "ready" if whisper_available else "unavailable", # Whisper 품질 검증 상태
            "audio_quality_analysis": "ready" if librosa_available else "unavailable", # 오디오 품질 분석 상태
            "ffmpeg_video_composition": "ready" if ffmpeg_available else "unavailable", # FFmpeg 비디오 합성 상태
            "cogvideox_text_to_video": "ready" if COGVIDEODX_AVAILABLE else "unavailable", # CogVideoX-2b T2V 상태
            "riffusion_bgm": "ready" if RIFFUSION_AVAILABLE else "unavailable", # Riffusion BGM 상태
            "enhanced_musical_bgm": "ready" if ffmpeg_available else "unavailable" # FFmpeg 기반 BGM 가용성
        },
        "capabilities": { # 서버의 주요 기능 가용성
            "video_generation": COGVIDEODX_AVAILABLE, # 비디오 생성 가능 여부
            "voice_generation": bool(os.getenv("OPENAI_API_KEY")), # 음성 생성 가능 여부 (API 키 존재 여부)
            "enhanced_bgm_generation": RIFFUSION_AVAILABLE, # 향상된 BGM 생성 가능 여부
            "brand_optimization": True, # 브랜드 최적화 기능 사용 여부
            "video_composition": ffmpeg_available, # 비디오 합성 가능 여부
            "complete_30sec_workflow": all([ # 30초 완성 워크플로우 전체 가용성 (모든 필수 서비스 필요)
                COGVIDEODX_AVAILABLE,
                os.getenv("OPENAI_API_KEY"),
                ffmpeg_available
            ])
        },
        "video_composition": { # 비디오 합성 관련 상세 정보
            "ffmpeg_available": ffmpeg_available, # FFmpeg 사용 가능 여부
            "cogvideox_available": COGVIDEODX_AVAILABLE, # CogVideoX 사용 가능 여부
            "supported_resolutions": ["1920x1080", "1280x720", "854x480"], # 지원 해상도
            "supported_formats": ["mp4", "avi", "mov"], # 지원 포맷
            "default_video_quality": "medium", # 기본 비디오 품질
            "video_extension_supported": False # 비디오 확장 기능 지원 여부 (예시)
        },
        "quality_validation": { # 품질 검증 관련 상세 정보
            "whisper_available": whisper_available, # Whisper 사용 가능 여부
            "whisper_error": whisper_error, # Whisper 오류 메시지
            "librosa_available": librosa_available, # Librosa 사용 가능 여부
            "supported_whisper_models": supported_models, # 지원되는 Whisper 모델 목록
            "total_available_models": len(supported_models), # 총 사용 가능 모델 수
            "default_quality_threshold": 0.8 # 기본 품질 임계값
        },
        "bgm_generation": { # BGM 생성 관련 상세 정보
            "riffusion_available": RIFFUSION_AVAILABLE, # Riffusion 사용 가능 여부
            "enhanced_musical_bgm_available": ffmpeg_available, # FFmpeg 기반 BGM 사용 가능 여부
            "chord_based_harmonies": ffmpeg_available, # 화음 기반 BGM 가능 여부 (FFmpeg으로 구현 시)
            "rhythm_patterns": ffmpeg_available, # 리듬 패턴 가능 여부 (FFmpeg으로 구현 시)
            "style_specific_harmonies": ffmpeg_available, # 스타일별 화음 가능 여부 (FFmpeg으로 구현 시)
            "riffusion_model_generation": RIFFUSION_PIPELINE_AVAILABLE, # Riffusion 모델을 통한 생성 가능 여부
            "fallback_system": True, # 폴백 시스템 사용 여부
            "default_bgm_volume": 0.25 # 기본 BGM 볼륨
        },
        "brand_optimization": { # 브랜드 최적화 관련 상세 정보
            "supported_brands": list(BRAND_PRESETS.keys()), # 지원 브랜드 목록
            "enhanced_prompts": True, # 강화된 프롬프트 사용 여부
            "brand_validation": True, # 브랜드 검증 사용 여부
            "visual_scenarios": True # 시각적 시나리오 사용 여부
        },
        "improvements_v321": [ # 최근 개선 사항 목록
            "파일 존재 확인 강화",
            "FFmpeg 타임아웃 추가",
            "OpenAI 클라이언트 싱글톤 패턴",
            "에러 핸들링 개선",
            "Task 상태 업데이트 최적화"
        ],
        "active_tasks": len([t for t in tasks_storage.values() if t.get("status") == "processing"]), # 현재 처리 중인 작업 수
        "total_completed_tasks": len([t for t in tasks_storage.values() if t.get("status") == "completed"]) # 총 완료된 작업 수
    }

@app.get("/api/v1/video/ffmpeg-status") # FFmpeg 상태 엔드포인트: FFmpeg 설치 여부 및 가이드 제공.
async def get_ffmpeg_status():
    """FFmpeg 설치 상태 확인"""
    ffmpeg_available = check_ffmpeg_availability() # FFmpeg 가용성 체크
    
    return { # FFmpeg 상태를 JSON 응답으로 반환
        "ffmpeg_available": ffmpeg_available, # FFmpeg 사용 가능 여부
        "cogvideox_available": COGVIDEODX_AVAILABLE, # CogVideoX 사용 가능 여부
        "enhanced_bgm_available": ffmpeg_available, # 향상된 BGM 사용 가능 여부 (FFmpeg 기반)
        "install_guide": { # FFmpeg 설치 가이드
            "windows": "winget install --id=Gyan.FFmpeg -e 또는 choco install ffmpeg (관리자 권한)",
            "macos": "brew install ffmpeg (Homebrew 설치 필요)",
            "ubuntu": "sudo apt update && sudo apt install ffmpeg",
            "conda": "conda install -c conda-forge ffmpeg (Conda 환경 내)"
        },
        "test_command": "ffmpeg -version", # 테스트 명령어
        "message": "FFmpeg 사용 가능 (향상된 BGM 지원)" if ffmpeg_available else "FFmpeg가 설치되지 않았습니다. 위의 가이드를 참조하여 설치해주세요." # 메시지
    }

# ─────────────────────────────────────────────
# 6) 품질 검증 관련 엔드포인트들
# ─────────────────────────────────────────────

@app.get("/api/v1/quality/settings", response_model=QualityValidationSettings) # 품질 검증 설정 엔드포인트
async def get_quality_validation_settings():
    """음성 품질 검증 시스템의 현재 설정 및 가용성 정보 조회."""
    
    whisper_available = False # Whisper 가용성 초기화
    whisper_error = None # 오류 메시지 초기화
    supported_models = [] # 지원 모델 목록 초기화
    
    try: # Whisper 모듈 임포트 및 모델 목록 조회
        import whisper
        whisper_available = True
        supported_models = get_available_whisper_models() # 사용 가능한 Whisper 모델 목록 가져오기
    except Exception as e:
        whisper_error = str(e) # 오류 메시지 저장
        supported_models = [] # 목록 비우기
    
    return QualityValidationSettings( # 품질 검증 설정 반환
        whisper_available=whisper_available, # Whisper 사용 가능 여부
        supported_models=supported_models, # 지원 모델 목록
        default_settings={ # 기본 설정 값
            "min_quality_score": 0.8,
            "max_retry_attempts": 2,
            "whisper_model": "base",
            "enable_quality_validation": True,
            "quality_analysis_available": whisper_available
        }
    )

@app.post("/api/v1/quality/test") # 품질 검증 테스트 엔드포인트
async def test_quality_validation(test_text: str = "안녕하세요. 테스트 음성입니다."):
    """음성 품질 검증 시스템의 작동 여부 테스트."""
    
    if not os.getenv("OPENAI_API_KEY"): # OpenAI API 키 없으면 에러
        raise HTTPException(status_code=400, detail="OpenAI API 키가 설정되지 않았습니다.")
    
    try:
        from app.agents.agents import EnhancedAudioGeneratorAgent # 오디오 생성 에이전트 임포트
        
        test_dir = os.path.join(os.getcwd(), "test_audio") # 테스트 오디오 저장 디렉토리
        os.makedirs(test_dir, exist_ok=True) # 디렉토리 생성 (없으면 생성)
        
        test_agent = EnhancedAudioGeneratorAgent( # 테스트용 오디오 생성 에이전트 초기화
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            audio_dir=test_dir,
            enable_quality_validation=True,
            max_retry_attempts=1
        )
        
        test_storyboard = { # 테스트용 스토리보드 (단일 씬)
            "scenes": [
                {
                    "name": "Test Scene",
                    "narration": test_text,
                    "description": "Quality validation test"
                }
            ]
        }
        
        result = await test_agent.generate_narrations_with_validation( # 음성 생성 및 검증 실행 (await 필요)
            test_storyboard, 
            voice="alloy",
            min_quality_score=0.7
        )
        
        if result and result[0].get("file") and os.path.exists(result[0]["file"]): # 테스트 후 생성 파일 정리
            try:
                os.remove(result[0]["file"]) # 임시 파일 삭제
            except Exception:
                pass # 삭제 실패 시 무시
        
        return { # 테스트 결과 반환
            "test_successful": True, # 테스트 성공 여부
            "message": "품질 검증 시스템이 정상 작동합니다.", # 결과 메시지
            "test_result": {
                "audio_generated": bool(result and result[0].get("file")), # 오디오 생성 여부
                "quality_validated": bool(result and result[0].get("quality_validation", {}).get("available")), # 품질 검증 여부
                "quality_score": result[0].get("quality_validation", {}).get("overall_score", 0) if result else 0, # 품질 점수
                "test_text": test_text # 테스트 텍스트
            }
        }
        
    except Exception as e: # 테스트 실패 시 에러 반환
        return {
            "test_successful": False, # 테스트 실패 여부
            "error": str(e), # 에러 메시지
            "message": "품질 검증 시스템 테스트 실패" # 실패 메시지
        }

# ─────────────────────────────────────────────
# 7) 광고 생성 백그라운드 작업들
# ─────────────────────────────────────────────

# 기존 광고 생성 엔드포인트 (하위 호환성): 예전 버전의 광고 생성 로직.
async def process_ad_generation(task_id: str, request_data: dict):
    """기존 광고 생성 워크플로우 (이미지 + 음성 + 비디오) - T2V 모델 적용 (현재 미구현/플레이스홀더)."""
    pass # 실제 구현은 이 안에. (현재 기능 미구현)

# 30초 완성 광고 생성의 실제 비동기 처리 함수: 핵심 광고 생성 로직.
async def process_complete_ad_generation(task_id: str, request_data: dict):
    """
    30초 완성 광고 생성을 위한 통합 워크플로우 (CogVideoX-2b + TTS + 향상된 BGM).
    이 함수는 백그라운드에서 실행됩니다.
    """
    try:
        # 워크플로우 초기화: AI 모델/클라이언트가 아직 로드되지 않았다면 로드.
        global ai_workflow
        if ai_workflow is None:
            initialize_workflow() # AI 워크플로우 초기화

        update_task_status(task_id, status="processing", progress=5, current_step="광고 컨셉 구상 중...") # 상태 업데이트 (5%)

        api_key = os.getenv("OPENAI_API_KEY") # OpenAI API 키 로드
        if not api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.") # 키 없으면 에러 발생

        # 에이전트 임포트: 필요한 에이전트(컨셉 생성, 오디오 생성) 클래스 임포트.
        from app.agents.agents import ConceptGeneratorAgent, EnhancedAudioGeneratorAgent # 에이전트 임포트
        
        # 1. 광고 컨셉 및 나레이션, 영상 설명 생성: LLM(GPT-4o-mini) 호출하여 광고 컨셉 생성.
        update_task_status(task_id, progress=10, current_step="광고 컨셉 및 나레이션/영상 설명 생성 중...") # 상태 업데이트 (10%)
        
        keywords_str = request_data["keywords"] # 키워드 문자열 (CompleteAdRequest 기준)

        complete_concept_prompt = get_complete_ad_concept_prompt( # 전체 광고 컨셉 프롬프트 생성
            request_data["brand"],
            keywords_str,
            request_data["target_audience"],
            request_data["style_preference"],
            request_data["duration"]
        )

        # LLM 호출: OpenAI API를 통해 광고 컨셉 (나레이션, 영상 설명) 생성.
        openai_client = await get_openai_client() # 비동기 OpenAI 클라이언트 가져오기
        chat_completion = await openai_client.chat.completions.create( # LLM 호출 (await 필요)
            model="gpt-4o-mini", # 사용할 모델 지정
            response_format={"type": "json_object"}, # 응답을 JSON 형식으로 받도록 지시
            messages=[
                {"role": "system", "content": "You are an expert ad creator. Respond with a JSON object."},
                {"role": "user", "content": complete_concept_prompt}
            ],
            temperature=0.7 # 창의성 조절
        )
        try: # LLM 응답 파싱 및 유효성 검사
            ad_concept = json.loads(chat_completion.choices[0].message.content) # JSON 파싱
            if not ad_concept or not ad_concept.get("narration") or not ad_concept.get("visual_description"):
                raise ValueError("LLM 응답에서 나레이션 또는 영상 설명이 누락되었습니다.") # 필수 필드 누락 시 에러
        except json.JSONDecodeError as e: # JSON 파싱 실패 시
            raise Exception(f"LLM 응답 JSON 파싱 실패: {e}. 원시 응답: {chat_completion.choices[0].message.content}")
        except ValueError as e: # 유효성 검사 실패 시
            raise Exception(f"LLM 응답 유효성 검사 실패: {e}")

        tasks_storage[task_id]["ad_concept"] = ad_concept # 생성된 컨셉 저장
        update_task_status(task_id, progress=25, current_step="광고 컨셉 생성 완료") # 상태 업데이트 (25%)

        # 2. 나레이션 음성 생성 및 품질 검증: 생성된 나레이션 텍스트로 음성 파일 생성 및 품질 확인.
        update_task_status(task_id, progress=30, current_step="고품질 나레이션 음성 생성 및 검증 중...") # 상태 업데이트 (30%)
        audio_dir = os.path.join(os.getcwd(), "generated/audio", task_id) # 오디오 저장 디렉토리 설정
        os.makedirs(audio_dir, exist_ok=True) # 디렉토리 생성

        quality_options = { # 음성 품질 검증 옵션
            "enable_quality_validation": request_data.get("enable_quality_validation", True),
            "max_retry_attempts": request_data.get("max_retry_attempts", 2),
            "min_quality_score": request_data.get("min_quality_score", 0.8)
        }
        
        audio_agent = EnhancedAudioGeneratorAgent( # 음성 생성 에이전트 초기화
            openai_api_key=api_key, 
            audio_dir=audio_dir,
            enable_quality_validation=quality_options["enable_quality_validation"],
            max_retry_attempts=quality_options["max_retry_attempts"]
        )

        narration_text = ad_concept["narration"] # 생성된 광고 컨셉에서 나레이션 텍스트 추출
        
        temp_storyboard = {"scenes": [{"name": "Ad Narration", "narration": narration_text, "description": ad_concept.get("visual_description", "")}]} # 단일 나레이션을 위한 임시 스토리보드 구조.

        # ✅ 수정: 올바른 메서드 호출 (await 없이 - 동기 함수)
        validated_audio_result = audio_agent.generate_narrations_with_validation(
            temp_storyboard, 
            voice=request_data.get("voice", "nova"),
            min_quality_score=quality_options["min_quality_score"]
        )
        
        if not validated_audio_result or not validated_audio_result[0].get("file"):
            raise Exception("나레이션 음성 생성 또는 품질 검증 실패.") # 음성 생성 실패 시 에러
        
        audio_path = validated_audio_result[0]["file"] # 생성된 오디오 파일 경로
        tasks_storage[task_id]["audio_path"] = audio_path # 작업 저장소에 오디오 경로 저장
        tasks_storage[task_id]["quality_report"] = validated_audio_result[0].get("quality_validation", {}) # 품질 보고서 저장
        update_task_status(task_id, progress=50, current_step="나레이션 음성 생성 및 검증 완료") # 상태 업데이트 (50%)

        # 3. CogVideoX-2b 비디오 및 Riffusion BGM 생성: 텍스트 프롬프트로 비디오와 BGM 생성.
        update_task_status(task_id, progress=55, current_step="AI 비디오 및 BGM 생성 중...") # 상태 업데이트 (55%)
        
        video_dir_output = os.path.join(os.getcwd(), "generated", "videos", task_id) # 비디오 저장 디렉토리
        bgm_dir_output = os.path.join(os.getcwd(), "generated", "bgm", task_id) # BGM 저장 디렉토리
        os.makedirs(video_dir_output, exist_ok=True) # 디렉토리 생성
        os.makedirs(bgm_dir_output, exist_ok=True) # 디렉토리 생성
        
        video_path = None # 비디오 경로 초기화
        bgm_path = None # BGM 경로 초기화

        if COGVIDEODX_AVAILABLE: # CogVideoX가 사용 가능한 경우
            try:
                optimized_prompt = optimize_zeroscope_prompt_enhanced( # CogVideoX용 최적화 프롬프트 생성
                    request_data["brand"],
                    ad_concept["visual_description"], 
                    keywords_str,
                    request_data["style_preference"]
                )
                
                validated_prompt = validate_brand_prompt(request_data["brand"], optimized_prompt) # 프롬프트 최종 검증 (브랜드 관련 요소 포함 확인)
                
                print(f"🎯 CogVideoX-2b 최적화된 비디오 프롬프트: {validated_prompt}")
                
                # CogVideoXGenerator 인스턴스 생성 시 'cog_utils.' 접두사 사용
                cogvideox_generator = cog_utils.CogVideoXGenerator(output_dir=video_dir_output, bgm_dir=bgm_dir_output) # CogVideoX 생성기 인스턴스 생성
                
                video_path, bgm_path = await cogvideox_generator.generate_video_from_prompt( # 비디오/BGM 생성 실행 (await 필요)
                    prompt=validated_prompt, # 비디오 생성 프롬프트
                    duration=request_data["duration"], # 영상 길이
                    quality=request_data.get("video_quality", "balanced"), # 비디오 품질
                    enable_bgm=request_data.get("enable_bgm", False), # BGM 생성 활성화 여부
                    bgm_prompt=request_data.get("bgm_prompt", keywords_str) # BGM 프롬프트
                )
                
                if video_path and os.path.exists(video_path): # 비디오 생성 성공 여부 확인
                    print(f"✅ CogVideoX-2b 비디오 생성 성공: {video_path}")
                    if bgm_path: # BGM 생성 성공 여부 확인
                        print(f"✅ Riffusion BGM 생성 성공: {bgm_path}")
                    else:
                        print("⚠️ Riffusion BGM 생성 실패 또는 비활성화됨.")
                else:
                    raise Exception("CogVideoX-2b 비디오 생성 실패 또는 파일 없음") # 비디오 파일 생성 실패 시 에러
                    
            except Exception as e: # 비디오/BGM 생성 중 예외 처리
                print(f"❌ CogVideoX-2b 또는 Riffusion BGM 생성 실패: {e}. 전체 작업을 실패 처리합니다.")
                raise Exception(f"비디오 및 BGM 생성 실패 (CogVideoX 오류): {e}")
        else: # CogVideoX 사용 불가 시 에러
            raise Exception("CogVideoX-2b 모듈을 로드할 수 없어 비디오 생성 기능을 사용할 수 없습니다. `enable_t2v`를 False로 설정하거나 환경을 확인하세요.")

        tasks_storage[task_id]["video_path"] = video_path # 생성된 비디오 경로 저장
        tasks_storage[task_id]["bgm_path"] = bgm_path # 생성된 BGM 경로 저장
        update_task_status(task_id, progress=80, current_step="AI 비디오 및 BGM 생성 완료") # 상태 업데이트 (80%)

        # 4. 최종 영상 합성: 생성된 비디오, 나레이션 오디오, BGM을 합쳐 최종 광고 영상 생성.
        update_task_status(task_id, progress=90, current_step="최종 광고 영상 합성 중...") # 상태 업데이트 (90%)
        
        final_dir = os.path.join(os.getcwd(), "generated", "final", task_id) # 최종 영상 저장 디렉토리
        os.makedirs(final_dir, exist_ok=True) # 디렉토리 생성
        
        final_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 최종 파일명용 타임스탬프
        brand_safe = request_data["brand"].replace(" ", "_").replace("/", "_") # 안전한 브랜드명 (파일 경로용)
        final_output = os.path.join(final_dir, f"final_ad_{brand_safe}_{request_data['duration']}s_{final_timestamp}.mp4") # 최종 출력 경로
                
        try: # FFmpeg를 이용한 최종 합성
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", # 덮어쓰기 허용
                        "-i", video_path, # 입력 비디오
                        "-i", audio_path, # 입력 나레이션 오디오
                    ]
                    
                    if bgm_path and os.path.exists(bgm_path): # BGM이 있다면
                        ffmpeg_cmd.extend([
                            "-i", bgm_path, # 입력 BGM 오디오
                            "-filter_complex", # 복합 필터 시작
                            "[1:a]volume=1.0[voice];[2:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=shortest[audio_mix]", # 나레이션과 BGM 믹싱
                            "-map", "0:v", # 첫 번째 입력(비디오)의 영상 스트림 선택
                            "-map", "[audio_mix]", # 믹싱된 오디오 스트림 선택
                        ])
                    else: # BGM이 없으면 나레이션만 사용
                        ffmpeg_cmd.extend([
                            "-filter_complex", # 복합 필터 시작
                            "[1:a]volume=1.0[audio_mix]", # 나레이션만 사용
                            "-map", "0:v", # 첫 번째 입력(비디오)의 영상 스트림 선택
                            "-map", "[audio_mix]", # 오디오 스트림 선택
                        ])

                    ffmpeg_cmd.extend([ # 공통 인코딩 옵션
                        "-c:v", "libx264", "-c:a", "aac", # 비디오/오디오 코덱 지정
                        "-preset", "medium", "-crf", "23", # 인코딩 품질 설정
                        "-movflags", "+faststart", # 웹 최적화
                        "-t", str(request_data["duration"]), # 최종 영상 길이
                        final_output # 최종 출력 파일
                    ])
                    
                    print(f"🎬 FFmpeg 명령어: {' '.join(ffmpeg_cmd)}")  # 디버깅용 출력
                    
                    result_ffmpeg = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True, timeout=300) # FFmpeg 실행 및 타임아웃 300초
                    
                    if not os.path.exists(final_output): # 최종 파일 생성 여부 확인
                        raise Exception("최종 영상 파일이 생성되지 않았습니다.")
                    
                    file_size = os.path.getsize(final_output) / (1024*1024) # 파일 크기 계산 (MB 단위)
                    print(f"✅ 최종 광고 영상 생성 완료: {final_output} ({file_size:.1f}MB)")
                    
        except subprocess.CalledProcessError as e: # FFmpeg 실행 중 에러
            print(f"❌ FFmpeg 합성 실패: {e.stderr}")
            raise Exception(f"영상 합성 실패: {e.stderr}")
        except subprocess.TimeoutExpired: # FFmpeg 시간 초과
            print("❌ FFmpeg 합성 시간 초과")
            raise Exception("영상 합성 시간 초과")

        # 최종 결과 저장: 작업 완료 후 결과 데이터 정리 및 저장.
        result = {
            "status": "completed", # 작업 상태 완료
            "message": f"🎉 '{request_data['brand']}' 브랜드 {request_data['duration']}초 완성 광고가 성공적으로 생성되었습니다!", # 완료 메시지
            "content": { # 생성된 광고 콘텐츠 정보
                "final_video": final_output, # 최종 비디오 파일 경로
                "ad_concept": ad_concept, # 생성된 광고 컨셉
                "components": { # 개별 구성 요소 경로
                    "video_path": video_path,
                    "audio_path": audio_path,
                    "bgm_path": bgm_path
                }
            },
            "metadata": { # 생성 메타데이터
                "brand": request_data["brand"],
                "duration": request_data["duration"],
                "style": request_data["style_preference"],
                "voice": request_data.get("voice", "nova"),
                "video_quality": request_data.get("video_quality", "balanced"),
                "bgm_enabled": bool(bgm_path), # BGM 활성화 여부
                "file_size_mb": round(os.path.getsize(final_output) / (1024*1024), 1), # 최종 파일 크기
                "generation_time": datetime.now().isoformat(), # 생성 완료 시간
                "model_used": "CogVideoX-2b + OpenAI TTS + Riffusion BGM" # 사용된 모델 정보
            }
        }

        update_task_status( # 작업 최종 상태 '완료'로 업데이트
            task_id,
            status="completed",
            progress=100,
            current_step="완료",
            result=result, # 최종 결과 저장
            completed_at=datetime.now().isoformat() # 완료 시간 기록
        )
        
        print(f"🎉 30초 완성 광고 생성 성공: {task_id}")

    except Exception as e: # 작업 중 예기치 못한 에러 발생 시 처리
        import traceback # 상세 에러 스택 트레이스 얻기 위함
        error_details = traceback.format_exc() # 에러 상세 내용
        update_task_status( # 작업 상태 '실패'로 업데이트
            task_id,
            status="failed",
            error=str(e), # 에러 메시지
            current_step="실패",
            error_details=error_details[:1000] # 에러 상세 내용 저장 (길이 제한)
        )
        print(f"❌ 30초 완성 광고 생성 실패: {task_id} - {e}") # 콘솔 출력

# ─────────────────────────────────────────────
# 8) 광고 생성 요청 및 상태/결과 조회 엔드포인트
# ─────────────────────────────────────────────

@app.post("/api/v1/ads/generate", response_model=TaskResponse) # 기존 광고 생성 엔드포인트 (하위 호환성)
async def generate_advertisement(request: AdGenerationRequest, background_tasks: BackgroundTasks):
    """기존 광고 생성 (이미지 + 음성 + 비디오)"""
    if not request.brand or not request.keywords: # 필수 입력 검증
        raise HTTPException(status_code=400, detail="브랜드명과 키워드는 필수 입력 항목입니다.")

    task_id = str(uuid.uuid4()) # 고유 작업 ID 생성
    tasks_storage[task_id] = { # 작업 저장소에 초기 정보 등록
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "current_step": "대기 중...",
        "created_at": datetime.now().isoformat(),
        "request_data": request.dict()
    }
    
    background_tasks.add_task(process_ad_generation, task_id, request.dict()) # 백그라운드 태스크로 실제 작업 시작

    return TaskResponse(task_id=task_id, status="queued", message=f"광고 생성 작업이 시작되었습니다. 작업 ID: {task_id}") # 응답 반환

@app.post("/api/v1/ads/create-complete", response_model=TaskResponse) # 새로운 30초 완성 광고 생성 엔드포인트
async def create_complete_advertisement(request: CompleteAdRequest, background_tasks: BackgroundTasks):
    """🎉 30초 완성 광고 영상 생성 v3.3 (CogVideoX-2b + TTS + 향상된 BGM + 브랜드 최적화)"""
    
    if not request.brand or not request.keywords: # 필수 입력 검증
        raise HTTPException(status_code=400, detail="브랜드명과 키워드는 필수입니다.")
    
    missing_services = [] # 필수 서비스 가용성 체크 리스트
    if not os.getenv("OPENAI_API_KEY"):
        missing_services.append("OpenAI API (TTS용)")
    if not COGVIDEODX_AVAILABLE:
        missing_services.append("CogVideoX-2b (텍스트-투-비디오용)")
    if not check_ffmpeg_availability():
        missing_services.append("FFmpeg (영상 처리용)")
    
    if missing_services: # 누락된 서비스 있으면 에러 반환
        raise HTTPException(
            status_code=400, 
            detail=f"필수 서비스가 설치되지 않았습니다: {', '.join(missing_services)}" # 누락된 서비스 목록 포함하여 에러 메시지 반환
        )

    task_id = str(uuid.uuid4()) # 고유 작업 ID 생성
    tasks_storage[task_id] = { # 작업 저장소에 초기 정보 등록
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "current_step": "대기 중...",
        "created_at": datetime.now().isoformat(),
        "request_data": request.dict() # 요청 데이터 저장
    }
    
    # process_complete_ad_generation 함수 호출: 백그라운드 태스크로 광고 생성 로직 실행.
    background_tasks.add_task(process_complete_ad_generation, task_id, request.dict()) # 비동기 백그라운드 작업으로 등록
    
    return TaskResponse( # 응답 반환
        task_id=task_id,
        status="queued",
        message=f"🎬 '{request.brand}' 브랜드 {request.duration}초 완성 광고 생성이 시작되었습니다! (v3.3 CogVideoX-2b + 향상된 BGM + 브랜드 최적화) 작업 ID: {task_id}"
    )

@app.get("/api/v1/ads/status/{task_id}", response_model=TaskStatusResponse) # 작업 상태 조회 엔드포인트
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    if task_id not in tasks_storage: # 작업 ID 없으면 에러
        raise HTTPException(status_code=404, detail="요청된 작업을 찾을 수 없습니다.") # 404 Not Found 에러 반환
    return TaskStatusResponse(**tasks_storage[task_id]) # 작업 상태 정보 반환

@app.get("/api/v1/ads/result/{task_id}") # 작업 결과 조회 엔드포인트
async def get_task_result(task_id: str):
    """작업 결과 조회"""
    if task_id not in tasks_storage: # 작업 ID 없으면 에러
        raise HTTPException(status_code=404, detail="요청된 작업을 찾을 수 없습니다.")
    task = tasks_storage[task_id] # 해당 작업 정보 가져오기
    if task["status"] != "completed": # 완료되지 않았으면 에러
        raise HTTPException(status_code=400, detail=f"작업이 아직 완료되지 않았습니다. 현재 상태: {task['status']}") # 400 Bad Request 에러 반환
    
    return { # 완료된 작업 결과 반환
        "task_id": task_id,
        "status": "completed",
        "result": task["result"], # 작업 결과 데이터
        "metadata": { # 작업 메타데이터
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
            "request_data": task["request_data"]
        }
    }

# ─────────────────────────────────────────────
# 9) 작업 목록 조회 엔드포인트
# ─────────────────────────────────────────────
@app.get("/api/v1/tasks") # 모든 작업 목록 조회 엔드포인트
async def list_tasks(limit: int = 10, offset: int = 0):
    """작업 목록 조회 (페이지네이션 지원)."""
    all_tasks = list(tasks_storage.values()) # 모든 작업 가져오기
    sorted_tasks = sorted(all_tasks, key=lambda x: x["created_at"], reverse=True) # 생성 시간 기준으로 최신순 정렬
    return {"tasks": sorted_tasks[offset:offset+limit], "total": len(all_tasks), "limit": limit, "offset": offset} # 페이지네이션 적용된 결과 반환

# ─────────────────────────────────────────────
# 10) 다운로드 엔드포인트
# ─────────────────────────────────────────────
@app.get("/download/{task_id}") # 최종 광고 영상 다운로드 엔드포인트
async def download_final_video(task_id: str):
    """최종 광고 영상 다운로드."""
    if task_id not in tasks_storage: # 작업 ID 없으면 에러
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    task = tasks_storage[task_id] # 해당 작업 정보 가져오기
    if task["status"] != "completed": # 완료되지 않았으면 에러
        raise HTTPException(status_code=400, detail="작업이 완료되지 않았습니다.")
    
    if "final_video" in task["result"]["content"]: # 최종 광고 (CogVideoX로 생성된 것)
        final_video = task["result"]["content"]["final_video"] # 최종 비디오 경로
        if not os.path.exists(final_video): # 파일 없으면 에러
            raise HTTPException(status_code=404, detail="영상 파일을 찾을 수 없습니다.")
        
        filename = f"{task['request_data']['brand']}_{task['request_data']['duration']}sec_ad_{task_id[:8]}.mp4" # 다운로드 파일명 생성
        return FileResponse( # 파일 응답 반환
            final_video,
            media_type="video/mp4", # 미디어 타입 지정
            filename=filename # 다운로드 파일명 지정
        )
    
    elif "videos" in task["result"]["content"] and task["result"]["content"]["videos"]: # 기존 광고 (첫 번째 비디오 반환)
        video_path = task["result"]["content"]["videos"][0] # 첫 번째 비디오 경로
        if not os.path.exists(video_path): # 파일 없으면 에러
            raise HTTPException(status_code=404, detail="영상 파일을 찾을 수 없습니다.")
        
        filename = f"{task['request_data']['brand']}_ad_{task_id[:8]}.mp4" # 다운로드 파일명 생성
        return FileResponse( # 파일 응답 반환
            video_path,
            media_type="video/mp4",
            filename=filename
        )
    
    else: # 다운로드 가능한 영상 파일이 없을 때
        raise HTTPException(status_code=404, detail="다운로드 가능한 영상 파일이 없습니다.")

@app.get("/api/v1/brands/presets") # 브랜드 프리셋 조회 엔드포인트
async def get_brand_presets():
    """지원하는 브랜드 프리셋 목록 조회."""
    return { # 브랜드 프리셋 정보 반환
        "supported_brands": list(BRAND_PRESETS.keys()), # 지원 브랜드 이름 목록
        "presets": BRAND_PRESETS,      # 브랜드별 프리셋 상세 정보
        "total_brands": len(BRAND_PRESETS), # 총 지원 브랜드 수
        "message": "브랜드별 최적화된 프리셋을 제공합니다." # 안내 메시지
    }

@app.get("/api/v1/bgm/styles") # BGM 스타일 조회 엔드포인트
async def get_bgm_styles():
    """지원하는 BGM 스타일 목록 조회."""
    return { # BGM 스타일 정보 반환
        "supported_styles": ["모던하고 깔끔한", "따뜻하고 아늑한", "미니멀하고 프리미엄한", "역동적이고 에너지", "감성적이고 로맨틱"], # 지원 스타일 목록
        "enhanced_musical_bgm": check_ffmpeg_availability(), # 향상된 BGM(FFmpeg 기반) 가능 여부
        "riffusion_available": RIFFUSION_AVAILABLE, # Riffusion BGM 가능 여부
        "features": { # BGM 기능 특징
            "chord_progressions": True, # 코드 진행 지원
            "rhythm_patterns": True, # 리듬 패턴 지원
            "style_specific_harmonies": True, # 스타일별 화음 지원
            "riffusion_model_generation": RIFFUSION_PIPELINE_AVAILABLE, # Riffusion 모델 생성 지원
            "fallback_system": True # 폴백 시스템 사용 여부
        },
        "message": "AI 기반 BGM 생성을 지원합니다." # 안내 메시지
    }

@app.exception_handler(Exception) # 글로벌 예외 핸들러: 모든 처리되지 않은 예외를 잡아서 500 에러 응답.
async def global_exception_handler(request: Request, exc: Exception):
    """API 요청 처리 중 발생하는 모든 예외를 캐치하여 500 Internal Server Error 응답 반환."""
    print(f"💥 서버 에러 발생: {exc}") # 에러 로그 출력
    import traceback # 상세 스택 트레이스 얻기
    print(traceback.format_exc()) # 스택 트레이스 출력
    return JSONResponse(status_code=500, content={"detail": f"서버 내부 오류가 발생했습니다: {exc}"}) # 500 에러 응답 반환

# ─────────────────────────────────────────────
# 11) 서버 실행
# ─────────────────────────────────────────────
if __name__ == "__main__": # 스크립트 직접 실행 시 Uvicorn 서버 시작
    import uvicorn # Uvicorn 임포트
    print("🚀 AI 30초 완성 광고 크리에이터 서버 v3.3을 시작합니다...") # 시작 메시지
    print("🎯 NEW: CogVideoX-2b 통합 (짧은 클립 생성 및 합성) + Riffusion BGM + 브랜드 최적화!") # 새로운 기능 설명
    print("🎵 특징: Riffusion 기반 BGM, CogVideoX-2b 프롬프트 최적화, 브랜드 검증") # 주요 특징
    print("📋 엔드포인트:") # 사용 가능한 API 엔드포인트 안내
    print("     - GET       /                  : 웹 인터페이스")
    print("     - POST      /api/v1/ads/create-complete : 🆕 30초 완성 광고 생성 v3.3")
    print("     - POST      /api/v1/ads/generate    : 기존 광고 생성 (T2V 폴백)")
    print("     - GET       /api/v1/brands/presets  : 🆕 브랜드 프리셋 조회")
    print("     - GET       /api/v1/bgm/styles      : 🆕 BGM 스타일 조회")
    print("     - GET       /docs                   : API 문서")
    print("     - GET       /download/{task_id}     : 완성된 30초 영상 다운로드")
    print("🎬 v3.3 개선사항: CogVideoX-2b 통합, Riffusion BGM, 엔디비아 최적화, 품질검증 강화") # 버전별 개선사항 요약
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) # Uvicorn 서버 실행 (reload=True는 코드 변경 시 자동 재시작)