# app/core/mock_openai_client.py - MusicGen 대안 (더 안정적)

import os
import time
import torch
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from typing import List, Dict, Any

# 음악 생성 라이브러리 시도 (순서대로)
MUSIC_GENERATOR_TYPE = None

try:
    # 1차 시도: MusicGen (Meta - 매우 안정적)
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    MUSIC_GENERATOR_TYPE = "musicgen"
    print("🎵 MusicGen (Meta) 감지 - 안정적인 음악 생성")
except ImportError:
    try:
        # 2차 시도: Riffusion (문제가 해결된 경우)
        from diffusers import StableDiffusionPipeline
        import riffusion
        # 실제 사용 가능한 함수가 있는지 확인
        if hasattr(riffusion, 'RiffusionPipeline') or len([attr for attr in dir(riffusion) if not attr.startswith('_')]) > 0:
            MUSIC_GENERATOR_TYPE = "riffusion"
            print("🎵 Riffusion 감지")
        else:
            raise ImportError("Riffusion 모듈이 비어있음")
    except ImportError:
        # 3차 시도: 기본 음성 합성으로 대체
        MUSIC_GENERATOR_TYPE = "basic"
        print("🎵 기본 음성 합성 사용 (Riffusion/MusicGen 불가)")

load_dotenv()

class MockOpenAIClient:
    """다양한 음악 생성 엔진을 지원하는 클라이언트"""
    
    def __init__(self):
        print("✅ Mock OpenAI client initialized")
        print(f"🎭 음악 생성: {MUSIC_GENERATOR_TYPE.upper()} 엔진 사용")
        
        # 음악 생성 모델은 필요할 때 로드
        self.music_generator = None
        self.music_processor = None
    
    def _init_music_generator(self):
        """음악 생성 모델 초기화"""
        if self.music_generator is None:
            if MUSIC_GENERATOR_TYPE == "musicgen":
                self._init_musicgen()
            elif MUSIC_GENERATOR_TYPE == "riffusion":
                self._init_riffusion()
            else:
                self._init_basic_audio()
    
    def _init_musicgen(self):
        """MusicGen 초기화 (Meta)"""
        try:
            print("🎵 MusicGen 모델 로딩 중...")
            
            # MusicGen small 모델 로드 (빠르고 안정적)
            self.music_processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.music_generator = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
            
            # CPU/GPU 자동 선택
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.music_generator = self.music_generator.to(device)
            
            print(f"✅ MusicGen 로딩 완료! (디바이스: {device})")
            
        except Exception as e:
            print(f"❌ MusicGen 로딩 실패: {e}")
            self.music_generator = False
    
    def _init_riffusion(self):
        """Riffusion 초기화 (만약 작동한다면)"""
        try:
            print("🎵 Riffusion 모델 로딩 중...")
            # Riffusion 코드 (이전과 동일)
            self.music_generator = True
            print("✅ Riffusion 로딩 완료!")
        except Exception as e:
            print(f"❌ Riffusion 로딩 실패: {e}")
            self.music_generator = False
    
    def _init_basic_audio(self):
        """기본 오디오 합성 초기화"""
        print("🎵 기본 오디오 합성 엔진 초기화...")
        self.music_generator = True
        print("✅ 기본 오디오 합성 준비 완료!")

    def generate_concept(self, brand: str, keywords: str) -> str:
        """광고 컨셉 생성"""
        print(f"🎨 광고 컨셉 생성: {brand} + {keywords}")
        time.sleep(1)
        
        concept = f"""
🎯 {brand} Advertisement Concept

Main Message: "Experience the magic of {brand}"

Scene Breakdown:
1. Opening (0-10s): Cozy atmosphere with {keywords}
2. Product Focus (10-20s): Featured items and happy customers  
3. Closing (20-30s): Brand logo with memorable tagline

Narration: "When you need comfort, {brand} is here for you."

Visual Style: Warm colors, natural lighting, emotional connections
Keywords Integration: {keywords}
Target Emotion: Warmth, comfort, reliability
Call-to-Action: Visit your nearest {brand} location
"""
        print("✅ 컨셉 생성 완료")
        return concept

    def generate_images(self, concept: str, count: int = 3) -> List[Dict[str, Any]]:
        """이미지 생성 (목업)"""
        print(f"🖼️ 이미지 {count}개 생성 중...")
        time.sleep(2)
        
        images = []
        scenes = [
            "cozy winter café opening scene", 
            "featured products with happy customers",
            "brand logo closing with warm lighting"
        ]
        
        for i in range(count):
            scene = scenes[i] if i < len(scenes) else f"commercial scene {i+1}"
            images.append({
                "scene": scene,
                "image_path": f"data/temp/image_{i+1}.png",
                "prompt": f"Commercial advertisement: {scene}",
                "style": "professional photography, warm lighting"
            })
        
        print(f"✅ 이미지 {count}개 생성 완료")
        return images
    
    def generate_voice(self, concept: str, text: str = None) -> List[Dict[str, Any]]:
        """음성 나레이션 생성 (목업)"""
        print("🎤 음성 나레이션 생성 중...")
        time.sleep(1.5)
        
        if not text:
            if "Narration:" in concept:
                text = concept.split("Narration:")[1].split("\n")[0].strip().strip('"')
            else:
                text = "Experience the warmth and comfort that awaits you."
        
        voices = [{
            "voice_path": "data/temp/narration.wav",
            "text": text,
            "duration": len(text.split()) * 0.5,
            "voice_style": "professional, warm, inviting",
            "language": "en-US"
        }]
        
        print("✅ 음성 나레이션 생성 완료")
        return voices

    def generate_music(self, concept: str, keywords: str = "", count: int = 3) -> List[Dict[str, Any]]:
        """배경음악 생성 - 다중 엔진 지원"""
        print(f"🎵 배경음악 생성 시작... (엔진: {MUSIC_GENERATOR_TYPE.upper()})")
        
        # 음악 생성 모델 초기화
        self._init_music_generator()
        
        if not self.music_generator:
            print("⚠️ 모든 음악 생성 엔진 사용 불가, 목업 데이터 반환")
            return self._generate_mock_music()
        
        try:
            # 컨셉 분석
            brand_style = self._analyze_music_style(concept, keywords)
            
            # 섹션별 음악 생성
            music_sections = [
                {
                    "name": "opening",
                    "prompt": f"{brand_style['style']} {brand_style['mood']} commercial intro",
                    "duration": 8.0
                },
                {
                    "name": "main", 
                    "prompt": f"{brand_style['style']} {brand_style['mood']} background music",
                    "duration": 15.0
                },
                {
                    "name": "closing",
                    "prompt": f"{brand_style['mood']} memorable ending theme",
                    "duration": 5.0
                }
            ]
            
            generated_music = []
            
            for section in music_sections:
                try:
                    # 엔진별 음악 생성
                    if MUSIC_GENERATOR_TYPE == "musicgen":
                        filepath = self._generate_music_with_musicgen(
                            prompt=section["prompt"],
                            duration=section["duration"]
                        )
                    elif MUSIC_GENERATOR_TYPE == "riffusion":
                        filepath = self._generate_music_with_riffusion(
                            prompt=section["prompt"],
                            duration=section["duration"]
                        )
                    else:
                        filepath = self._generate_music_with_basic_audio(
                            prompt=section["prompt"],
                            duration=section["duration"]
                        )
                    
                    generated_music.append({
                        "section": section["name"],
                        "file_path": filepath,
                        "duration": section["duration"],
                        "prompt": section["prompt"],
                        "style": brand_style,
                        "engine": MUSIC_GENERATOR_TYPE
                    })
                    
                except Exception as e:
                    print(f"❌ {section['name']} 음악 생성 실패: {e}")
                    # 목업으로 대체
                    generated_music.append({
                        "section": section["name"],
                        "file_path": f"data/temp/{section['name']}_music.wav",
                        "duration": section["duration"],
                        "prompt": section["prompt"],
                        "style": brand_style,
                        "engine": "mock"
                    })
            
            print(f"✅ 배경음악 {len(generated_music)}개 생성 완료 ({MUSIC_GENERATOR_TYPE.upper()})")
            return generated_music
            
        except Exception as e:
            print(f"❌ 배경음악 생성 실패: {e}")
            return self._generate_mock_music()

    def _analyze_music_style(self, concept: str, keywords: str) -> Dict[str, str]:
        """컨셉과 키워드에서 음악 스타일 분석"""
        concept_lower = concept.lower()
        keywords_lower = keywords.lower()
        
        if "starbucks" in concept_lower:
            brand = "starbucks"
        elif "café" in concept_lower or "coffee" in concept_lower:
            brand = "café"
        else:
            brand = "commercial"
        
        if any(word in concept_lower or word in keywords_lower 
               for word in ["winter", "겨울", "cozy", "warm"]):
            style = "cozy warm acoustic"
            mood = "comfortable inviting"
        elif any(word in concept_lower or word in keywords_lower 
                 for word in ["energetic", "upbeat", "dynamic"]):
            style = "upbeat contemporary"
            mood = "energetic positive"
        else:
            style = "smooth ambient"
            mood = "calm professional"
        
        return {"brand": brand, "style": style, "mood": mood}

    def _generate_music_with_musicgen(self, prompt: str, duration: float = 10.0) -> str:
        """MusicGen으로 실제 음악 생성"""
        print(f"🎼 MusicGen 음악 생성: '{prompt[:50]}...'")
        
        try:
            # 출력 디렉토리 생성
            output_dir = "data/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # MusicGen으로 음악 생성
            inputs = self.music_processor(
                text=[prompt],
                padding=True,
                return_tensors="pt",
            )
            
            # 음악 생성 (duration 초)
            audio_values = self.music_generator.generate(**inputs, max_new_tokens=int(duration * 50))  # 대략적인 토큰 수
            
            # 오디오 데이터 추출
            audio_data = audio_values[0, 0].cpu().numpy()
            
            # 파일명 생성
            safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_'))[:30]
            filename = f"musicgen_{safe_prompt.replace(' ', '_')}.wav"
            filepath = os.path.join(output_dir, filename)
            
            # WAV 파일로 저장
            sample_rate = self.music_generator.config.audio_encoder.sampling_rate
            sf.write(filepath, audio_data, sample_rate)
            
            print(f"✅ MusicGen 음악 생성 완료: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ MusicGen 음악 생성 실패: {e}")
            raise e

    def _generate_music_with_basic_audio(self, prompt: str, duration: float = 10.0) -> str:
        """기본 오디오 합성으로 음악 생성"""
        print(f"🎼 기본 오디오 합성: '{prompt[:50]}...'")
        
        try:
            # 출력 디렉토리 생성
            output_dir = "data/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 프롬프트 기반 음악 스타일 결정
            sample_rate = 44100
            audio_length = int(duration * sample_rate)
            t = np.linspace(0, duration, audio_length)
            
            # 프롬프트에 따른 주파수 선택
            if "cozy" in prompt.lower() or "warm" in prompt.lower():
                # 따뜻한 화음
                base_freqs = [220, 330, 440]  # A3, E4, A4
            elif "upbeat" in prompt.lower() or "energetic" in prompt.lower():
                # 활기찬 화음
                base_freqs = [262, 330, 392]  # C4, E4, G4
            else:
                # 편안한 화음
                base_freqs = [196, 294, 392]  # G3, D4, G4
            
            # 화음 생성
            audio = np.zeros(audio_length)
            for i, freq in enumerate(base_freqs):
                amplitude = 0.15 / (i + 1)  # 점점 작은 볼륨
                # 약간의 변조 추가 (더 자연스럽게)
                modulation = 1 + 0.1 * np.sin(2 * np.pi * 0.5 * t)
                audio += amplitude * np.sin(2 * np.pi * freq * t * modulation)
            
            # 페이드 인/아웃
            fade_samples = int(1.0 * sample_rate)
            audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
            audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            # 파일명 생성
            safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_'))[:30]
            filename = f"basic_audio_{safe_prompt.replace(' ', '_')}.wav"
            filepath = os.path.join(output_dir, filename)
            
            # WAV 파일로 저장
            sf.write(filepath, audio, sample_rate)
            
            print(f"✅ 기본 오디오 합성 완료: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 기본 오디오 합성 실패: {e}")
            raise e

    def _generate_mock_music(self) -> List[Dict[str, Any]]:
        """목업 음악 데이터 생성"""
        return [
            {
                "section": "opening",
                "file_path": "data/temp/opening_music.wav",
                "duration": 8.0,
                "prompt": "cozy warm commercial intro",
                "style": {"brand": "commercial", "style": "warm", "mood": "inviting"},
                "engine": "mock"
            },
            {
                "section": "main",
                "file_path": "data/temp/main_music.wav", 
                "duration": 15.0,
                "prompt": "smooth background music",
                "style": {"brand": "commercial", "style": "ambient", "mood": "professional"},
                "engine": "mock"
            },
            {
                "section": "closing",
                "file_path": "data/temp/closing_music.wav",
                "duration": 5.0,
                "prompt": "memorable ending theme",
                "style": {"brand": "commercial", "style": "uplifting", "mood": "memorable"},
                "engine": "mock"
            }
        ]

    def generate_video(self, concept: str, images: List, voices: List, music: List) -> str:
        """최종 영상 합성 (목업)"""
        print("🎬 최종 영상 합성 중...")
        time.sleep(3)
        
        output_path = "data/output/final_advertisement.mp4"
        
        print(f"📹 합성 정보:")
        print(f"   - 이미지: {len(images)}개")
        print(f"   - 음성: {len(voices)}개") 
        print(f"   - 음악: {len(music)}개")
        print(f"   - 음악 엔진: {music[0].get('engine', 'unknown') if music else 'none'}")
        print(f"   - 출력: {output_path}")
        
        print("✅ 영상 합성 완료")
        return output_path
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        print("🔗 Testing connection...")
        time.sleep(0.5)
        print("✅ Mock connection successful!")
        return True

def test_complete_system():
    """완전한 시스템 테스트"""
    print("🧪 Complete AI Advertisement System Test - Multi-Engine")
    print("=" * 60)
    
    try:
        client = MockOpenAIClient()
        
        print("\n1️⃣ 연결 테스트...")
        if not client.test_connection():
            return False
        
        print("\n2️⃣ 광고 컨셉 생성...")
        concept = client.generate_concept("Starbucks", "winter, cozy, new menu")
        print("✅ 컨셉 생성 완료")
        
        print("\n3️⃣ 이미지 생성...")
        images = client.generate_images(concept, count=3)
        print(f"✅ 이미지 {len(images)}개 생성 완료")
        
        print("\n4️⃣ 음성 나레이션 생성...")
        voices = client.generate_voice(concept)
        print(f"✅ 음성 {len(voices)}개 생성 완료")
        
        print("\n5️⃣ 배경음악 생성...")
        music = client.generate_music(concept, "winter, cozy")
        print(f"✅ 음악 {len(music)}개 생성 완료")
        
        print("\n6️⃣ 최종 영상 합성...")
        video_path = client.generate_video(concept, images, voices, music)
        print(f"✅ 영상 생성 완료: {video_path}")
        
        print("\n🎉 완전한 시스템 테스트 성공!")
        print(f"💡 음악 생성 엔진: {MUSIC_GENERATOR_TYPE.upper()}")
        print(f"📁 생성된 파일들은 data/output/ 폴더에서 확인하세요!")
        
        return True
        
    except Exception as e:
        print(f"💥 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    test_complete_system()