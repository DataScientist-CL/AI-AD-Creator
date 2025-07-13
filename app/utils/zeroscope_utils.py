import os
import torch
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from diffusers import DiffusionPipeline
    from diffusers.utils import export_to_video
    import imageio
    import imageio_ffmpeg # videoio 대신 imageio-ffmpeg 사용
    ZEROSCOPE_AVAILABLE = True
    print("✅ Zeroscope V2 모듈 로드 성공")
except ImportError as e:
    ZEROSCOPE_AVAILABLE = False
    print(f"❌ Zeroscope V2 모듈 로드 실패: {e}")
    print("📌 다음 명령어로 설치하세요:")
    print("pip install diffusers transformers accelerate")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("pip install imageio imageio-ffmpeg")


class ZeroscopeGenerator:

    """Zeroscope V2 Text-to-Video 생성기"""

    # Zeroscope V2 모델 ID
    MODEL_ID_XL = "cerspense/zeroscope_v2_XL" # 더 큰 모델, 고품질
    MODEL_ID_STANDARD = "cerspense/zeroscope_v2_576w" # <--- 이 부분을 수정합니다! (기존: "cerspense/zeroscope_v2_576_320")

    def __init__(self, output_dir: str = "generated/videos", use_xl_model: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pipeline = None
        self.is_initialized = False
        self.use_xl_model = use_xl_model # 이 값에 따라 self.model_id가 결정됨
        self.model_id = self.MODEL_ID_XL if use_xl_model else self.MODEL_ID_STANDARD # <--- Standard 모델 사용
        
        if ZEROSCOPE_AVAILABLE:
            self._check_system_requirements()
    

    def _check_system_requirements(self) -> bool:
        """시스템 요구사항 확인"""
        if not torch.cuda.is_available():
            print("❌ CUDA GPU가 필요합니다. Zeroscope V2는 GPU 없이는 매우 느립니다.")
            return False
        
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_memory < 12 and self.use_xl_model: # XL 모델은 더 많은 메모리 요구
            print(f"⚠️ 경고: XL 모델 사용 시 GPU 메모리({gpu_memory:.1f}GB)가 부족할 수 있습니다. 최소 12GB 권장.")
            print("💡 작은 모델(use_xl_model=False)을 사용하거나 GPU 메모리를 확보하세요.")
        elif gpu_memory < 6 and not self.use_xl_model: # Standard 모델 메모리 요구
             print(f"⚠️ 경고: Standard 모델 사용 시 GPU 메모리({gpu_memory:.1f}GB)가 부족할 수 있습니다. 최소 6GB 권장.")
        
        return True

    def initialize_pipeline(self) -> bool:
        """Zeroscope V2 파이프라인 초기화"""
        if not ZEROSCOPE_AVAILABLE:
            print("❌ Zeroscope V2 모듈이 설치되지 않았습니다.")
            return False
        
        if self.is_initialized:
            return True
        
        try:
            print(f"🔄 Zeroscope V2 파이프라인 로딩 중... ({self.model_id})")
            
            # 파이프라인 로드 시 device_map="auto"를 사용하여 자동 메모리 분배 활성화
            # local_files_only=False 추가하여 누락된 모델 파일 재다운로드 시도
            self.pipeline = DiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
                local_files_only=False # <--- 추가: 모델 파일 누락 문제 해결 시도
            )
            
            # GPU로 이동 및 메모리 최적화
            if torch.cuda.is_available():
                # self.pipeline = self.pipeline.to("cuda") # <--- 제거: 이 줄은 더 이상 필요 없습니다.
                print("🚀 GPU 가속 활성화 및 메모리 최적화 (자동 분배)")
                
                # device_map="auto"가 대부분의 메모리 관리를 처리하므로
                # 아래 명시적인 offload 호출은 필수는 아닐 수 있으나, 추가 최적화를 위해 유지 가능합니다.
                self.pipeline.enable_vae_slicing() 
                self.pipeline.enable_attention_slicing(1)
                self.pipeline.enable_model_cpu_offload() # 필요에 따라 유지
                self.pipeline.enable_sequential_cpu_offload() # 필요에 따라 유지
                
            else:
                print("⚠️ GPU를 찾을 수 없습니다. CPU 모드로 실행됩니다. 매우 느릴 수 있습니다.")
            
            self.is_initialized = True
            print("✅ Zeroscope V2 파이프라인 초기화 완료")
            return True
            
        except Exception as e:
            print(f"❌ Zeroscope V2 파이프라인 초기화 실패: {e}")
            self.pipeline = None
            return False

    def generate_video_from_prompt(self, 
                                   prompt: str, 
                                   duration: int = 30, # 요청된 길이
                                   quality: str = "balanced") -> Optional[str]:
        """
        텍스트 프롬프트로 직접 Zeroscope V2 비디오 생성
        
        Args:
            prompt: 비디오 생성 프롬프트
            duration: 요청된 비디오 길이 (초) - Zeroscope V2는 이 길이를 고려하여 생성
            quality: 품질 설정 ("fast", "balanced", "high")
            
        Returns:
            생성된 비디오 파일 경로
        """
        if not self.initialize_pipeline():
            return None
        
        # 🔧 수정됨: 메모리 정리 추가
        import gc
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        
        # 품질 설정에 따른 파라미터 조정
        generation_params = self._get_quality_params(quality, duration)
        
        print(f"🎬 Zeroscope V2 비디오 생성 시작... (목표 길이: {duration}초)")
        print(f"📋 설정: {generation_params['num_inference_steps']}단계, {generation_params['num_frames']}프레임, {generation_params['fps']}fps, {generation_params['width']}x{generation_params['height']} 해상도")
        
        try:
            # Zeroscope V2로 비디오 생성
            video_frames = self.pipeline(
                prompt=prompt,
                num_inference_steps=generation_params['num_inference_steps'],
                num_frames=generation_params['num_frames'],
                guidance_scale=generation_params['guidance_scale'],
                width=generation_params['width'],
                height=generation_params['height'],
                generator=torch.Generator(device="cuda").manual_seed(42) if torch.cuda.is_available() else None
            ).frames[0]
            
            # 🔧 수정됨: 생성 후 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            gc.collect()
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"zeroscope_{duration}s_{timestamp}.mp4"
            
            # 비디오 파일로 내보내기
            export_to_video(video_frames, str(output_path), fps=generation_params['fps'])
            
            # 실제 파일 정보 확인
            file_size = output_path.stat().st_size / (1024*1024)
            actual_frames = len(video_frames)
            actual_duration = actual_frames / generation_params['fps']
            
            print(f"✅ Zeroscope V2 비디오 생성 완료: {output_path}")
            print(f"📊 실제 결과: {actual_frames}프레임, {actual_duration:.1f}초, {file_size:.1f}MB")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Zeroscope V2 비디오 생성 중 오류: {e}")
            raise

    def _get_quality_params(self, quality: str, target_duration: int) -> Dict[str, Any]:
        """
        품질 설정과 목표 길이에 따른 생성 파라미터 반환 (🔧 수정됨)
        """
        # Zeroscope V2는 num_frames로 직접 길이를 조절합니다.
        # FPS는 기본 8~10 정도로 설정하는 것이 일반적이며, 여기서는 8로 고정합니다.
        base_fps = 8 
        
        # 🔧 수정됨: 프레임 수 계산 공식 완전 수정 (7초 → 30초 문제 해결)
        # 기존: num_frames = max(24, max(12, target_duration * 2))  # ← 이것이 문제였음!
        # 수정: 실제 duration에 맞는 프레임 수 계산
        num_frames = min(256, max(24, target_duration * base_fps))  # 30초 → 240프레임, 최대 256프레임 제한
        
        quality_configs = {
            "fast": {
                "num_inference_steps": 15,  # 🔧 수정됨: 20 → 15 (더 빠르게)
                "guidance_scale": 12.0,     # 🔧 수정됨: 5.0 → 12.0 (프롬프트 강화)
                "width": 384,
                "height": 256
            },
            "balanced": {
                "num_inference_steps": 20,
                "guidance_scale": 15.0,     # 🔧 수정됨: 12.5 → 15.0 (프롬프트 더 강화)
                "width": 576,
                "height": 320
            },
            "high": {
                "num_inference_steps": 25,
                "guidance_scale": 17.5,     # 🔧 수정됨: 7.0 → 17.5 (프롬프트 최대 강화)
                "width": 768,
                "height": 432
            }
        }
        
        config = quality_configs.get(quality, quality_configs["balanced"])
        
        # XL 모델 사용 시 해상도 조정
        if self.use_xl_model:
            if quality == "fast": # XL 모델에서는 fast도 해상도 좀 높게
                config["width"] = 576
                config["height"] = 320
            elif quality == "balanced":
                config["width"] = 768
                config["height"] = 432
            elif quality == "high":
                config["width"] = 1024
                config["height"] = 576 # 16:9 ratio
        
        config["num_frames"] = num_frames
        config["fps"] = base_fps
        config["expected_duration"] = num_frames / base_fps # 예상 실제 길이
        
        # 🔧 수정됨: 로그 메시지 개선
        print(f"🎥 수정된 설정: '{quality}' 품질, 목표 {target_duration}초 → {config['expected_duration']:.1f}초 영상 ({config['num_frames']}프레임)")
        return config

def check_zeroscope_installation():
    """Zeroscope V2 설치 상태 확인"""
    return {
        "zeroscope_available": ZEROSCOPE_AVAILABLE,
        "cuda_available": torch.cuda.is_available() if ZEROSCOPE_AVAILABLE else False,
        "gpu_memory": torch.cuda.get_device_properties(0).total_memory / (1024**3) if ZEROSCOPE_AVAILABLE and torch.cuda.is_available() else 0,
        "model_in_use": ZeroscopeGenerator().model_id if ZEROSCOPE_AVAILABLE else "N/A", # 현재 사용 모델
        "installation_guide": {
            "pytorch": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
            "diffusers": "pip install diffusers transformers accelerate",
            "video_utils": "pip install imageio imageio-ffmpeg",
            "note": "CUDA GPU와 최소 6GB VRAM 필요 (XL 모델은 12GB 이상 권장)"
        },
        "recommended_settings": {
            "fast": "15단계, 낮은 해상도 (빠른 생성, 메모리 절약)",  # 🔧 수정됨: 20→15
            "balanced": "20단계, 중간 해상도 (균형 잡힌 생성, 권장)", 
            "high": "25단계, 높은 해상도 (고품질 생성, 메모리 많이 사용)"
        },
        "duration_capability": "Zeroscope V2는 요청된 'duration'을 바탕으로 더 긴 영상을 직접 생성합니다. (단, 프레임 수/FPS에 의해 최종 길이가 결정됨)",
        "model_choices": {
            "XL_model": "cerspense/zeroscope_v2_XL (더 높은 퀄리티, 더 많은 GPU VRAM 필요)",
            "Standard_model": "cerspense/zeroscope_v2_576w (더 빠름, 적은 GPU VRAM)"  # 🔧 수정됨: 모델명 수정
        }
    }

# 편의 함수들 (main.py에서 직접 호출하지 않으므로 변경 불필요)
def generate_ad_video_zeroscope(prompt: str, duration: int = 30, quality: str = "balanced") -> Optional[str]:
    """간단한 Zeroscope V2 광고 비디오 생성 함수"""
    generator = ZeroscopeGenerator()
    return generator.generate_video_from_prompt(prompt, duration=duration, quality=quality)