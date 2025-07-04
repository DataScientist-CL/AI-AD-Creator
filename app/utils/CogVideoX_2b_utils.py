# app/utils/CogVideoX_2b_utils.py 파일 내용

import os # OS 기능 (파일/경로 조작)
import subprocess # 외부 프로세스 실행 (FFmpeg 등)
import math # 수학 함수 (나눗셈 올림 등) - 추가 임포트
import shutil # 파일/디렉토리 조작용 임포트 추가
from pathlib import Path # 파일 시스템 경로 객체 지향적 처리
from datetime import datetime # 날짜/시간 처리
from typing import Optional, Dict, Any, List # 타입 힌트

# PyTorch 임포트 및 가용성 플래그: 딥러닝 프레임워크 PyTorch 로드.
try:
    import torch # PyTorch 라이브러리 임포트 시도
    TORCH_AVAILABLE = True # 성공 시 True
except ImportError as e:
    TORCH_AVAILABLE = False # 실패 시 False
    print(f"❌ PyTorch 로드 실패: {e}")

# Diffusers 임포트 및 RiffusionPipeline 가용성 플래그: 확산 모델 라이브러리 로드.
# diffusers 임포트 수정 (RiffusionPipeline 직접 임포트 시도 부분 제거)
try:
    from diffusers import DiffusionPipeline # 기본 확산 파이프라인 임포트
    from diffusers.utils import export_to_video # 비디오 내보내기 유틸리티 임포트

    # RIFFUSION_PIPELINE_AVAILABLE은 이제 initialize_riffusion_pipeline()에서 설정할 것임
    # 따라서 여기서 RiffusionPipeline 임포트 시도 블록을 제거합니다.
    RIFFUSION_PIPELINE_AVAILABLE = True # 초기에는 True로 두고, 초기화 함수에서 실제 여부 판단
    
    DIFFUSERS_AVAILABLE = True # Diffusers 모듈 사용 가능
    print("✅ Diffusers 모듈 로드 성공")
except ImportError as e:
    DIFFUSERS_AVAILABLE = False # Diffusers 모듈 사용 불가능
    RIFFUSION_PIPELINE_AVAILABLE = False # Diffusers 자체가 없으면 Riffusion도 불가
    print(f"❌ Diffusers 모듈 로드 실패: {e}")
    print("📌 CogVideoX-2b 기능 없이 기본 이미지+오디오 합성 모드로 실행됩니다.")


# ImageIO 임포트 및 가용성 플래그: 이미지/비디오 파일 처리 라이브러리.
try:
    import imageio # imageio 라이브러리 임포트 시도
    import imageio_ffmpeg # imageio-ffmpeg 플러그인 임포트 시도
    IMAGEIO_AVAILABLE = True # 성공 시 True
except ImportError as e:
    IMAGEIO_AVAILABLE = False # 실패 시 False
    print(f"❌ ImageIO 로드 실패: {e}")

# SoundFile 임포트 및 가용성 플래그: 오디오 파일 저장 라이브러리 (Riffusion 결과 저장에 필요).
try:
    import soundfile as sf # soundfile 라이브러리 임포트 시도 (sf 별칭)
    SOUNDFILE_AVAILABLE = True # 성공 시 True
except ImportError as e:
    SOUNDFILE_AVAILABLE = False # 실패 시 False
    print(f"❌ SoundFile 로드 실패 (Riffusion BGM 저장 불가): {e}")
    print("📌 'pip install soundfile'을 실행하세요.")

# BGM 생성 전체 가용성 플래그: Riffusion 파이프라인과 SoundFile 모두 있어야 BGM 생성 가능.
BGM_GENERATION_AVAILABLE = RIFFUSION_PIPELINE_AVAILABLE and SOUNDFILE_AVAILABLE # Riffusion BGM 생성 가능 여부 최종 판단

# CogVideoX-2b 전체 가용성 확인: PyTorch, Diffusers, ImageIO 모두 있어야 CogVideoX 기능 활성화.
COGVIDEODX_AVAILABLE = TORCH_AVAILABLE and DIFFUSERS_AVAILABLE and IMAGEIO_AVAILABLE # CogVideoX-2b 기능 가능 여부 최종 판단

# CogVideoX-2b 의존성 로드 결과 출력 및 미설치 시 가이드 제공.
if COGVIDEODX_AVAILABLE:
    print("✅ CogVideoX-2b 기본 의존성 로드 성공")
else:
    print("❌ CogVideoX-2b 일부 기본 의존성 누락")
    print("📌 다음 명령어로 수정하세요:")
    if not TORCH_AVAILABLE: # PyTorch가 없으면 설치 가이드
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    if not DIFFUSERS_AVAILABLE: # Diffusers가 없으면 설치 가이드
        print("pip install 'numpy<2.0.0' --force-reinstall") # numpy 버전 충돌 방지
        print("pip install --upgrade huggingface-hub diffusers transformers accelerate")
    if not IMAGEIO_AVAILABLE: # ImageIO가 없으면 설치 가이드
        print("pip install imageio imageio-ffmpeg")
    if not SOUNDFILE_AVAILABLE: # SoundFile이 없으면 설치 가이드
        print("pip install soundfile")

class CogVideoXGenerator:
    """CogVideoX-2b Text-to-Video 생성기: 비디오 및 BGM 생성 로직."""

    MODEL_ID_COGVIDEODX = "THUDM/CogVideoX-2b" # CogVideoX 모델 ID
    RIFFUSION_MODEL_ID = "riffusion/riffusion-beta" # Riffusion 모델 ID

    def __init__(self, output_dir: str = "generated/videos", bgm_dir: str = "generated/bgm"):
        self.output_dir = Path(output_dir) # 비디오 출력 디렉토리 경로
        self.output_dir.mkdir(parents=True, exist_ok=True) # 디렉토리 생성 (없으면)
        self.bgm_dir = Path(bgm_dir) # BGM 출력 디렉토리 경로
        self.bgm_dir.mkdir(parents=True, exist_ok=True) # 디렉토리 생성 (없으면)

        self.pipeline = None # CogVideoX 파이프라인 객체 (초기 None)
        self.riffusion_pipeline = None # Riffusion 파이프라인 객체 (초기 None)
        self.is_initialized = False # CogVideoX 파이프라인 초기화 여부 플래그
        self.riffusion_initialized = False # Riffusion 파이프라인 초기화 여부 플래그
        self.model_id = self.MODEL_ID_COGVIDEODX # 사용할 CogVideoX 모델 ID
        print(f"🔄 설정된 비디오 모델: {self.model_id}")

        if not COGVIDEODX_AVAILABLE: # CogVideoX 의존성이 불완전하면 경고
            print("⚠️ CogVideoX-2b 기본 의존성이 완전하지 않습니다. 기능이 제한됩니다.")
            return

        self._check_system_requirements() # 시스템 요구사항 (GPU 등) 확인

    def _check_system_requirements(self) -> bool:
        """GPU 전용 시스템 요구사항 확인: PyTorch, CUDA, GPU 메모리 등."""
        if not TORCH_AVAILABLE: # PyTorch 설치 여부 확인
            print("❌ PyTorch가 설치되지 않았습니다.")
            return False

        if not torch.cuda.is_available(): # CUDA GPU 가용성 확인
            print("❌ CUDA GPU가 필요합니다. CogVideoX-2b는 GPU 전용으로 실행됩니다.")
            print("🔧 CUDA 설치 가이드:") # CUDA 설치 가이드 제공
            print("    1. NVIDIA 드라이버 설치: https://www.nvidia.com/drivers")
            print("    2. CUDA Toolkit 설치: https://developer.nvidia.com/cuda-downloads")
            print("    3. PyTorch CUDA 버전 재설치:")
            print("      pip uninstall torch torchvision torchaudio")
            print("      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
            return False

        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3) # GPU 메모리 확인 (GB)
        gpu_name = torch.cuda.get_device_name(0) # GPU 이름 가져오기

        print(f"🚀 GPU 감지: {gpu_name} ({gpu_memory:.1f}GB VRAM)")

        if gpu_memory < 8: # GPU 메모리 부족 경고
            print(f"⚠️ 경고: GPU 메모리({gpu_memory:.1f}GB)가 부족합니다.")
            print("📌 최소 8GB VRAM 권장, 12GB 이상 권장")
            print("🔧 해결방법:") # 해결 방법 제시
            print("    - 품질을 'fast'로 설정")
            print("    - 다른 GPU 프로그램 종료")
            print("    - 시스템 재부팅")
        else: # GPU 메모리 충분
            print(f"✅ GPU 메모리 충분: {gpu_memory:.1f}GB VRAM")

        return True # 시스템 요구사항 충족

    def initialize_pipeline(self) -> bool: # 파이프라인 초기화 함수로 이름 변경 (CogVideoX 전용)
        """CogVideoX-2b 파이프라인 초기화 및 GPU 메모리 최적화."""
        if not COGVIDEODX_AVAILABLE: # CogVideoX 의존성이 없으면 초기화 불가
            print("❌ CogVideoX-2b 기본 의존성이 설치되지 않아 파이프라인 초기화가 불가능합니다.")
            return False

        if self.is_initialized: # 이미 초기화되었다면 바로 반환
            return True

        if not torch.cuda.is_available(): # GPU 없으면 경고
            print("❌ GPU를 찾을 수 없습니다. CogVideoX-2b는 GPU 전용입니다.")
            return False

        try:
            print(f"🔄 CogVideoX-2b GPU 파이프라인 로딩 중... ({self.model_id})")
            torch.cuda.empty_cache() # GPU 메모리 캐시 비움

            self.pipeline = DiffusionPipeline.from_pretrained( # CogVideoX 모델 로드
                self.model_id,
                torch_dtype=torch.float16, # 부동소수점 16비트 사용 (메모리 절약)
                use_safetensors=True, # 안전한 가중치 파일 형식 사용
                trust_remote_code=True, # 원격 코드 실행 허용 (필요한 경우)
            )
            device = torch.device("cuda") # 장치 지정 (GPU)
            self.pipeline = self.pipeline.to(device) # 파이프라인을 GPU로 이동

            # CogVideoX 전용 GPU 메모리 최적화: 다양한 메모리 절약 기법 적용.
            print("🔧 CogVideoX 전용 GPU 메모리 최적화 적용 중...")
            try:
                if hasattr(self.pipeline, 'enable_vae_slicing'): # VAE 슬라이싱 활성화 (메모리 절약)
                    self.pipeline.enable_vae_slicing()
                    print("✅ VAE 슬라이싱 활성화")
                elif hasattr(self.pipeline, 'vae') and hasattr(self.pipeline.vae, 'enable_slicing'): # 대안 VAE 슬라이싱
                    self.pipeline.vae.enable_slicing()
                    print("✅ VAE 슬라이싱 활성화 (대안 방법)")
                else:
                    print("⚠️ VAE 슬라이싱 미지원 - 건너뜀")
            except Exception as vae_error:
                print(f"⚠️ VAE 최적화 실패: {vae_error}")

            try:
                if hasattr(self.pipeline, 'enable_attention_slicing'): # 어텐션 슬라이싱 활성화 (메모리 절약)
                    self.pipeline.enable_attention_slicing("max") # 최대 절약 모드
                    print("✅ 어텐션 슬라이싱 활성화 (최대 절약 모드)")
                else:
                    print("⚠️ 어텐션 슬라이싱 미지원 - 건너뜀")
            except Exception as attention_error:
                print(f"⚠️ 어텐션 최적화 실패: {attention_error}")

            try:
                if hasattr(self.pipeline, 'enable_model_cpu_offload'): # CPU 오프로딩 활성화 (GPU 메모리 부족 시)
                    self.pipeline.enable_model_cpu_offload()
                    print("✅ CPU 오프로딩 활성화 (GPU 메모리 부족 시 적극 활용)")
                else:
                    print("⚠️ CPU 오프로딩 미지원")
            except Exception as offload_error:
                print(f"⚠️ CPU 오프로딩 설정 실패: {offload_error}")

            try:
                if hasattr(self.pipeline, 'enable_xformers_memory_efficient_attention'): # xFormers 최적화 활성화 (속도/메모리)
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    print("✅ xFormers 메모리 효율 어텐션 활성화")
                else:
                    print("⚠️ xFormers 미지원 - 기본 어텐션 사용")
            except Exception as xformers_error:
                print(f"⚠️ xFormers 최적화 실패: {xformers_error}")

            self.is_initialized = True # 파이프라인 초기화 완료 플래그

            if torch.cuda.is_available(): # GPU 메모리 사용량 출력
                allocated = torch.cuda.memory_allocated() / (1024**3) # 할당된 메모리 (GB)
                reserved = torch.cuda.memory_reserved() / (1024**3) # 예약된 메모리 (GB)
                print(f"📊 GPU 메모리: 할당 {allocated:.1f}GB, 예약 {reserved:.1f}GB")

            print("✅ CogVideoX-2b GPU 파이프라인 초기화 완료")
            return True

        except Exception as e: # 초기화 중 에러 발생 시
            if "out of memory" in str(e).lower(): # 메모리 부족 에러 처리
                print("❌ 초기화 중 GPU 메모리 부족 발생! 더 적극적인 최적화 모드로 재시도합니다.")
                print("🔧 해결방법:") # 해결 방법 제시
                print("    1. 다른 GPU 프로그램 종료")
                print("    2. 시스템 재부팅")
                try: # 메모리 절약 모드로 재시도
                    print("🔄 메모리 절약 모드로 재시도...")
                    torch.cuda.empty_cache() # 캐시 비우기

                    self.pipeline = DiffusionPipeline.from_pretrained( # 모델 재로드 (메모리 절약 옵션 추가)
                        self.model_id,
                        torch_dtype=torch.float16,
                        device_map=None, # 장치 맵핑 강제 해제
                        local_files_only=False,
                        low_cpu_mem_usage=True, # 추가: 낮은 CPU 메모리 사용 옵션
                        trust_remote_code=True
                    )
                    self.pipeline = self.pipeline.to("cuda") # GPU로 이동
                    # 더 적극적인 최적화 재적용
                    if hasattr(self.pipeline, 'enable_vae_slicing'):
                        self.pipeline.enable_vae_slicing()
                    if hasattr(self.pipeline, 'enable_attention_slicing'):
                        self.pipeline.enable_attention_slicing("max")
                    if hasattr(self.pipeline, 'enable_model_cpu_offload'):
                        self.pipeline.enable_model_cpu_offload()
                    if hasattr(self.pipeline, 'enable_xformers_memory_efficient_attention'):
                        try:
                            self.pipeline.enable_xformers_memory_efficient_attention()
                        except Exception:
                            pass
                    self.is_initialized = True # 초기화 완료
                    print("✅ 메모리 절약 모드로 파이프라인 초기화 성공")
                    return True
                except Exception as retry_error: # 재시도 실패
                    print(f"❌ 메모리 절약 모드로도 초기화 실패: {retry_error}")
                    return False
            elif "trust_remote_code" in str(e) or "Placeholder" in str(e): # 캐시/토크나이저 문제 처리 (Diffusers 오류)
                print("🔄 캐시 문제로 인한 강제 재다운로드 시도...")
                try: # 강제 재다운로드
                    self.pipeline = DiffusionPipeline.from_pretrained( # 모델 강제 재다운로드
                        self.model_id,
                        torch_dtype=torch.float16,
                        device_map=None,
                        local_files_only=False,
                        use_safetensors=True,
                        trust_remote_code=True,
                        force_download=True, # 강제 다운로드 옵션
                        resume_download=True # 이어서 다운로드 옵션
                    )
                    self.pipeline = self.pipeline.to("cuda") # GPU로 이동
                    self.is_initialized = True # 초기화 완료
                    print("✅ 강제 재다운로드로 초기화 성공")
                    return True
                except Exception as retry_error: # 강제 재다운로드 실패
                    print(f"❌ 강제 재다운로드도 실패: {retry_error}")
                    return False
            else: # 기타 초기화 실패
                print(f"❌ CogVideoX-2b 파이프라인 초기화 실패: {e}")
                print("🔧 가능한 해결책:") # 가능한 해결책 제시
                print("    1. transformers 업데이트: pip install --upgrade transformers")
                print("    2. diffusers 업데이트: pip install --upgrade diffusers")
                print("    3. HuggingFace 캐시 삭제 후 재시도")
                return False

    def initialize_riffusion_pipeline(self) -> bool:
        """Riffusion 파이프라인 초기화: BGM 생성을 위한 모델 로드."""
        global RIFFUSION_PIPELINE_AVAILABLE # 전역 플래그를 수정할 수 있도록 global 선언

        if not RIFFUSION_PIPELINE_AVAILABLE: # 상단에서 Diffusers 모듈이 아예 로드되지 않았다면
            print("❌ Diffusers 모듈 또는 Riffusion 지원이 없어 Riffusion BGM 기본 의존성이 설치되지 않았습니다.")
            return False
        
        if self.riffusion_initialized: # 이미 초기화되었다면 바로 반환
            return True

        if not torch.cuda.is_available(): # GPU 없으면 경고 (Riffusion은 GPU 권장)
            print("❌ GPU를 찾을 수 없습니다. Riffusion은 GPU가 권장됩니다.")
            RIFFUSION_PIPELINE_AVAILABLE = False # GPU 없으면 Riffusion 기능 비활성화
            return False

        try:
            print(f"🔄 Riffusion GPU 파이프라인 로딩 중... ({self.RIFFUSION_MODEL_ID})")
            torch.cuda.empty_cache() # GPU 메모리 캐시 비움

            self.riffusion_pipeline = DiffusionPipeline.from_pretrained( # Riffusion 모델 로드 (DiffusionPipeline 사용)
                self.RIFFUSION_MODEL_ID,
                torch_dtype=torch.float16, # 부동소수점 16비트 사용
                use_safetensors=True, # 안전한 가중치 파일 형식 사용
                trust_remote_code=True, # Riffusion 모델도 custom code를 포함할 수 있으므로 추가
            )
            device = torch.device("cuda") # 장치 지정 (GPU)
            self.riffusion_pipeline = self.riffusion_pipeline.to(device) # 파이프라인을 GPU로 이동
            
            # Riffusion 파이프라인 최적화 (필요시)
            if hasattr(self.riffusion_pipeline, 'enable_xformers_memory_efficient_attention'): # xFormers 최적화
                try:
                    self.riffusion_pipeline.enable_xformers_memory_efficient_attention()
                    print("✅ Riffusion xFormers 메모리 효율 어텐션 활성화")
                except Exception:
                    print("⚠️ Riffusion xFormers 미설치 - 기본 어텐션 사용")
            if hasattr(self.riffusion_pipeline, 'enable_model_cpu_offload'): # CPU 오프로딩
                self.riffusion_pipeline.enable_model_cpu_offload()
                print("✅ Riffusion CPU 오프로딩 활성화")

            self.riffusion_initialized = True # Riffusion 파이프라인 초기화 완료 플래그
            print("✅ Riffusion GPU 파이프라인 초기화 완료")
            return True

        except Exception as e: # Riffusion 초기화 실패
            print(f"❌ Riffusion 파이프라인 초기화 실패: {e}")
            print("🔧 가능한 해결책:") # 가능한 해결책 제시
            print("    1. diffusers 업데이트: pip install --upgrade diffusers")
            print("    2. HuggingFace 캐시 삭제 후 재시도")
            return False

    async def generate_riffusion_bgm(self, prompt: str, duration: int) -> Optional[str]: # BGM 생성 함수 (비동기)
        """Riffusion 모델로 배경 음악 생성: 여러 세그먼트 생성 후 FFmpeg으로 병합."""
        if not self.initialize_riffusion_pipeline(): # Riffusion 파이프라인 초기화 시도
            return None # 초기화 실패 시 None 반환

        global BGM_GENERATION_AVAILABLE # 전역 변수 BGM_GENERATION_AVAILABLE 사용
        if not BGM_GENERATION_AVAILABLE: # BGM 생성 불가하면 반환
            print("❌ Riffusion 파이프라인이 로드되지 않아 BGM 생성이 불가능합니다.")
            return None

        print(f"🎶 Riffusion BGM 생성 시작 (프롬프트: '{prompt}', 길이: {duration}초)")
        try:
            audio_segments_paths = [] # 생성된 오디오 세그먼트 경로 리스트
            segment_duration_s = 5 # Riffusion이 한 번에 생성하는 오디오 길이 (약 5초)
            num_segments_to_generate = math.ceil(duration / segment_duration_s) # 필요한 세그먼트 개수 계산

            for i in range(num_segments_to_generate): # 필요한 만큼 세그먼트 반복 생성
                print(f"    Riffusion 세그먼트 {i+1}/{num_segments_to_generate} 생성 중...")
                # Riffusion 파이프라인 호출 (오디오 데이터 반환)
                riff = self.riffusion_pipeline(prompt=prompt).audios[0] 
                
                segment_path = self.bgm_dir / f"riffusion_segment_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.wav" # 세그먼트 파일 경로
                sf.write(str(segment_path), riff, samplerate=44100) # WAV 파일로 저장
                audio_segments_paths.append(str(segment_path))

            if len(audio_segments_paths) > 1: # 여러 세그먼트가 생성되면 FFmpeg으로 병합
                combined_bgm_path = self.bgm_dir / f"riffusion_combined_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav" # 최종 병합 파일 경로
                concat_list_path = self.bgm_dir / f"concat_list_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt" # FFmpeg concat 리스트 파일

                with open(concat_list_path, "w") as f: # concat 리스트 파일 생성
                    for audio_seg_path in audio_segments_paths:
                        f.write(f"file '{Path(audio_seg_path).resolve()}'\n") # 각 오디오 파일의 절대 경로 기록
                
                ffmpeg_cmd_concat = [ # FFmpeg concat 명령
                    "ffmpeg", "-y",
                    "-f", "concat", # concat demuxer 사용 (파일 목록을 입력으로 받음)
                    "-safe", "0", # 안전 모드 비활성화 (필요시 - 경로에 특수문자가 있을 경우)
                    "-i", str(concat_list_path), # concat 리스트 파일 입력
                    "-c", "copy", # 스트림 복사 (재인코딩 없이 빠르게 병합)
                    str(combined_bgm_path) # 출력 파일
                ]
                
                subprocess.run(ffmpeg_cmd_concat, capture_output=True, text=True, check=True, timeout=180) # FFmpeg 실행 및 타임아웃
                
                for audio_seg_path in audio_segments_paths: # 임시 세그먼트 파일 삭제
                    os.remove(audio_seg_path)
                os.remove(concat_list_path) # concat 리스트 파일 삭제

                return str(combined_bgm_path) # 병합된 BGM 경로 반환
            else: # 세그먼트가 하나뿐인 경우 그대로 반환
                return str(audio_segments_paths[0])
        except Exception as e: # BGM 생성 실패 시
            print(f"❌ Riffusion BGM 생성 실패: {e}")
            return None # 실패 시 None 반환

    async def generate_video_from_prompt(self, # 비디오 생성 함수 (비동기)
                                         prompt: str,
                                         duration: int = 30,
                                         quality: str = "balanced",
                                         enable_bgm: bool = False,
                                         bgm_prompt: Optional[str] = None) -> Optional[tuple[str, Optional[str]]]:
        """텍스트 프롬프트로 CogVideoX-2b 비디오 생성 (BGM 선택적 추가)."""
        if not COGVIDEODX_AVAILABLE: # CogVideoX 사용 불가하면 실패
            print("❌ CogVideoX-2b 기본 의존성 누락으로 비디오 생성이 불가능합니다.")
            return None, None

        if not self.initialize_pipeline(): # CogVideoX 파이프라인 초기화 시도
            return None, None # 초기화 실패 시 None 반환

        if TORCH_AVAILABLE: # GPU 메모리 정리 (파이프라인 실행 전)
            import gc
            if torch.cuda.is_available():
                torch.cuda.empty_cache() # CUDA 캐시 비우기
                torch.cuda.synchronize() # GPU 작업 완료 대기
            gc.collect() # 가비지 컬렉션 실행

        generation_params = self._get_quality_params_cogvideox(quality) # 품질에 따른 생성 파라미터 설정

        base_fps = 8 # 기본 FPS (초당 프레임 수)
        num_frames = int(duration * base_fps) # 총 프레임 수 계산
        if num_frames < 16: # 최소 프레임 수 제한 (너무 짧은 영상 방지)
            num_frames = 16
            print(f"⚠️ 요청된 길이에 비해 프레임 수가 너무 적어 {num_frames}프레임으로 조정됩니다.")

        actual_expected_duration = num_frames / base_fps # 실제 생성될 예상 비디오 길이 (조정된 프레임 수 기준)

        print(f"🎬 CogVideoX-2b 비디오 생성 시작 (프롬프트: '{prompt}')") # 시작 메시지
        print(f"📋 설정: {generation_params['num_inference_steps']}단계, {num_frames}프레임, {base_fps}fps, 예상 길이: {actual_expected_duration:.1f}초")

        try:
            generator = torch.Generator(device="cuda").manual_seed(42) # GPU용 난수 생성기 (결과 재현성 위함)

            video_frames = self.pipeline( # CogVideoX 파이프라인 호출 (비디오 프레임 생성)
                prompt=prompt, # 텍스트 프롬프트
                num_inference_steps=generation_params['num_inference_steps'], # 추론 단계 수
                guidance_scale=generation_params['guidance_scale'], # 가이던스 스케일 (생성 품질/프롬프트 일치도)
                width=generation_params['width'], # 비디오 너비
                height=generation_params['height'], # 비디오 높이
                num_frames=num_frames, # 생성할 프레임 수
                generator=generator, # 난수 생성기
            ).frames # 생성된 비디오 프레임 (리스트 형태)

            if TORCH_AVAILABLE and torch.cuda.is_available(): # GPU 메모리 재정리 (생성 후)
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 파일명용 타임스탬프
            output_video_path = self.output_dir / f"cogvideox_generated_{int(actual_expected_duration)}s_{timestamp}.mp4" # 출력 비디오 경로

            # 🔧 수정된 비디오 저장 부분 (리스트 프레임 처리)
            try:
                # CogVideoX 출력 데이터 구조 분석
                print(f"🔍 비디오 프레임 타입: {type(video_frames)}")
                
                if isinstance(video_frames, list):
                    print(f"🔍 리스트 길이: {len(video_frames)}")
                    if len(video_frames) > 0:
                        print(f"🔍 첫 번째 요소 타입: {type(video_frames[0])}")
                        if hasattr(video_frames[0], 'shape'):
                            print(f"🔍 첫 번째 요소 형태: {video_frames[0].shape}")
                    
                    # 리스트에서 실제 프레임 배열 추출
                    if len(video_frames) > 0:
                        # 첫 번째 요소가 실제 프레임 배열인 경우
                        frames_data = video_frames[0]
                    else:
                        raise Exception("비디오 프레임 리스트가 비어있습니다.")
                else:
                    frames_data = video_frames
                
                # PyTorch 텐서를 numpy 배열로 변환
                if hasattr(frames_data, 'cpu'):
                    # PyTorch 텐서인 경우
                    video_frames_np = frames_data.cpu().numpy()
                    print("🔄 PyTorch 텐서를 numpy로 변환")
                elif hasattr(frames_data, 'numpy'):
                    # GPU 배열인 경우
                    video_frames_np = frames_data.numpy()
                    print("🔄 GPU 배열을 numpy로 변환")
                else:
                    # 이미 numpy이거나 다른 형태
                    video_frames_np = frames_data
                    print("🔄 기존 데이터 사용")
                
                # 최종 데이터 타입과 형태 확인
                print(f"🔍 최종 프레임 타입: {type(video_frames_np)}")
                if hasattr(video_frames_np, 'shape'):
                    print(f"🔍 최종 프레임 형태: {video_frames_np.shape}")
                    print(f"🔍 최종 프레임 데이터 타입: {video_frames_np.dtype}")
                
                # export_to_video 함수 호출
                export_to_video(video_frames_np, str(output_video_path), fps=base_fps)
                print("✅ export_to_video로 비디오 저장 성공")
                
            except Exception as export_error:
                print(f"❌ export_to_video 실패: {export_error}")
                print("🔄 대체 방법으로 비디오 저장 시도...")
                
                # 대체 방법: imageio를 직접 사용
                try:
                    import imageio
                    import numpy as np
                    
                    # 프레임 데이터 추출 및 변환
                    if isinstance(video_frames, list) and len(video_frames) > 0:
                        frames_data = video_frames[0]  # 리스트의 첫 번째 요소
                    else:
                        frames_data = video_frames
                    
                    # PyTorch 텐서를 numpy로 변환
                    if hasattr(frames_data, 'cpu'):
                        frames = frames_data.cpu().numpy()
                    elif hasattr(frames_data, 'numpy'):
                        frames = frames_data.numpy()
                    else:
                        frames = np.array(frames_data)
                    
                    print(f"🔍 대체 방법 - 원본 프레임 형태: {frames.shape}, 타입: {frames.dtype}")
                    
                    # 데이터 타입 정규화
                    if frames.dtype == np.float32 or frames.dtype == np.float64:
                        if frames.max() <= 1.0:
                            # 0-1 범위를 0-255로 변환
                            frames = (frames * 255).astype(np.uint8)
                            print("🔄 float [0-1] 범위를 uint8 [0-255]로 변환")
                        else:
                            # 이미 0-255 범위인 float
                            frames = frames.astype(np.uint8)
                            print("🔄 float을 uint8로 변환")
                    elif frames.dtype != np.uint8:
                        # 기타 정수 타입을 uint8로 변환
                        frames = frames.astype(np.uint8)
                        print(f"🔄 {frames.dtype}을 uint8로 변환")
                    
                    # 차원 조정
                    if len(frames.shape) == 5:
                        # (batch, frames, height, width, channels) -> (frames, height, width, channels)
                        frames = frames[0]
                        print("🔄 배치 차원 제거: (B,F,H,W,C) -> (F,H,W,C)")
                    elif len(frames.shape) == 4:
                        # (frames, height, width, channels) - 이미 올바른 형태
                        print("✅ 올바른 차원: (F,H,W,C)")
                    else:
                        print(f"⚠️ 예상치 못한 차원: {frames.shape}")
                    
                    print(f"🔍 최종 프레임 형태: {frames.shape}, 타입: {frames.dtype}")
                    
                    # imageio로 비디오 저장
                    print("🎬 imageio로 비디오 저장 중...")
                    with imageio.get_writer(str(output_video_path), mode='I', fps=base_fps, codec='libx264', quality=8) as writer:
                        for i, frame in enumerate(frames):
                            if i % 10 == 0:  # 진행상황 출력
                                print(f"  프레임 {i+1}/{len(frames)} 저장 중...")
                            writer.append_data(frame)
                    
                    print(f"✅ 대체 방법으로 비디오 저장 성공: {output_video_path}")
                    
                except Exception as fallback_error:
                    print(f"❌ 대체 비디오 저장도 실패: {fallback_error}")
                    
                    # 마지막 수단: 각 프레임을 이미지로 저장하고 ffmpeg로 합성
                    try:
                        print("🔄 마지막 수단: 프레임별 이미지 저장 후 ffmpeg 합성...")
                        
                        # 임시 프레임 디렉토리 생성
                        frames_dir = self.output_dir / f"temp_frames_{timestamp}"
                        frames_dir.mkdir(exist_ok=True)
                        
                        # 프레임 데이터 추출
                        if isinstance(video_frames, list) and len(video_frames) > 0:
                            frames_data = video_frames[0]
                        else:
                            frames_data = video_frames
                            
                        if hasattr(frames_data, 'cpu'):
                            frames = frames_data.cpu().numpy()
                        elif hasattr(frames_data, 'numpy'):
                            frames = frames_data.numpy()
                        else:
                            frames = np.array(frames_data)
                        
                        # 차원 및 타입 조정
                        if len(frames.shape) == 5:
                            frames = frames[0]
                        
                        if frames.dtype != np.uint8:
                            if frames.max() <= 1.0:
                                frames = (frames * 255).astype(np.uint8)
                            else:
                                frames = frames.astype(np.uint8)
                        
                        # 각 프레임을 PNG 이미지로 저장
                        frame_paths = []
                        for i, frame in enumerate(frames):
                            frame_path = frames_dir / f"frame_{i:04d}.png"
                            imageio.imwrite(str(frame_path), frame)
                            frame_paths.append(str(frame_path))
                        
                        print(f"📁 {len(frame_paths)}개 프레임 이미지 저장 완료")
                        
                        # ffmpeg로 이미지 시퀀스를 비디오로 변환
                        ffmpeg_cmd = [
                            "ffmpeg", "-y",
                            "-framerate", str(base_fps),
                            "-i", str(frames_dir / "frame_%04d.png"),
                            "-c:v", "libx264",
                            "-pix_fmt", "yuv420p",
                            "-crf", "23",
                            str(output_video_path)
                        ]
                        
                        subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True, timeout=300)
                        
                        # 임시 프레임 파일들 삭제
                        shutil.rmtree(str(frames_dir))
                        
                        print(f"✅ ffmpeg 합성으로 비디오 저장 성공: {output_video_path}")
                        
                    except Exception as final_error:
                        print(f"❌ 모든 비디오 저장 방법 실패: {final_error}")
                        raise Exception(f"비디오 저장 완전 실패 - export_to_video: {export_error}, imageio: {fallback_error}, ffmpeg: {final_error}")

            file_size = output_video_path.stat().st_size / (1024*1024) # 파일 크기 (MB)
            actual_frames = len(video_frames) # 실제 생성된 프레임 수
            actual_duration = actual_frames / base_fps # 실제 생성된 비디오 길이

            print(f"✅ CogVideoX-2b 비디오 생성 완료: {output_video_path}") # 성공 메시지
            print(f"📊 결과: {actual_frames}프레임, {actual_duration:.1f}초, {file_size:.1f}MB")

            bgm_output_path = None # BGM 출력 경로 초기화
            if enable_bgm and BGM_GENERATION_AVAILABLE: # BGM 활성화 및 가용성 체크
                actual_bgm_prompt = bgm_prompt if bgm_prompt else prompt # BGM 프롬프트 결정 (명시된 프롬프트 또는 비디오 프롬프트)
                bgm_output_path = await self.generate_riffusion_bgm(actual_bgm_prompt, duration) # BGM 생성 (await 필요)
                
                if not bgm_output_path: # BGM 생성 실패 시
                    print("⚠️ Riffusion BGM 생성 실패. BGM 없이 최종 영상 합성.")
            else: # BGM 비활성화 또는 Riffusion 불가 시
                print("⚠️ 배경 음악 기능이 비활성화되었거나 Riffusion이 사용 불가능합니다.")

            return str(output_video_path), bgm_output_path # 비디오 경로와 BGM 경로 반환 (튜플)

        except Exception as e: # 비디오 생성 중 예외 처리
            print(f"❌ CogVideoX-2b 비디오 생성 중 오류: {e}")
            raise # 예외 다시 발생 (호출자에게 전달)

    def _get_quality_params_cogvideox(self, quality: str) -> Dict:
        """RTX 4070에 최적화된 CogVideoX-2b 생성 파라미터 (품질별 설정)."""
        quality_configs = { # 품질별 (fast, balanced, high) 설정
            "fast": { # 빠른 생성 (낮은 품질, 적은 메모리)
                "num_inference_steps": 20, # 추론 단계 수
                "guidance_scale": 7.0, # 가이던스 스케일
                "width": 320, # 너비
                "height": 320 # 높이
            },
            "balanced": { # 균형 잡힌 생성
                "num_inference_steps": 30,
                "guidance_scale": 9.0,
                "width": 384,
                "height": 384
            },
            "high": { # 고품질 생성 (높은 메모리)
                "num_inference_steps": 40,
                "guidance_scale": 11.0,
                "width": 448,
                "height": 448
            }
        }
        
        config = quality_configs.get(quality, quality_configs["fast"]) # 선택 품질 없으면 'fast' 기본 적용
        print(f"🎥 CogVideoX-2b 설정: '{quality}' 품질, {config['num_inference_steps']}단계, {config['width']}x{config['height']}")
        return config # 설정 반환

# 간단한 CogVideoX-2b 광고 비디오 생성 함수 (독립형): 실제 Generator 클래스를 활용하는 헬퍼 함수.
async def generate_ad_video_cogvideox(prompt: str, duration: int = 30, quality: str = "balanced", enable_bgm: bool = False, bgm_prompt: Optional[str] = None) -> Optional[tuple[str, Optional[str]]]:
    """간단한 CogVideoX-2b 광고 비디오 생성 함수 (BGM 선택적 활성화)."""
    if not COGVIDEODX_AVAILABLE: # CogVideoX 사용 불가하면 스킵
        print("❌ CogVideoX-2b 기본 의존성이 완전하지 않아 비디오 생성을 건너뜁니다.")
        return None, None # 비디오 및 BGM 경로 모두 None 반환
    
    if enable_bgm and not BGM_GENERATION_AVAILABLE: # BGM 활성화인데 Riffusion 불가하면 경고
        print("⚠️ Riffusion BGM 기능이 활성화되었지만 RiffusionPipeline 또는 SoundFile을 로드할 수 없습니다. BGM 없이 진행합니다.")
        enable_bgm = False # BGM 비활성화 (BGM 생성이 불가능하므로)

    generator = CogVideoXGenerator() # CogVideoXGenerator 인스턴스 생성
    video_path, generated_bgm_path = await generator.generate_video_from_prompt(prompt, duration=duration, quality=quality, enable_bgm=enable_bgm, bgm_prompt=bgm_prompt) # 비디오 생성 실행 (await 필요)
    
    return video_path, generated_bgm_path # 비디오 경로와 BGM 경로 반환