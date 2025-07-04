# app/agents/agents.py

from typing import List, Dict, Any, Optional
import json
from openai import OpenAI
import os
import requests
import logging
import uuid # 이미지 파일명 생성을 위해 추가

import time
try:
    from .quality_validator import AudioQualityValidator
    QUALITY_VALIDATOR_AVAILABLE = True
except ImportError:
    QUALITY_VALIDATOR_AVAILABLE = False
    print("⚠️ AudioQualityValidator를 사용할 수 없습니다.")

# 로거 설정은 그대로 둡니다.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ConceptGeneratorAgent:
    """
    브랜드 + 키워드 → 광고 스토리보드(컨셉) 생성기
    """
    def __init__(self, prompt_template: str, api_key: Optional[str] = None):
        # 매개변수로 전달된 api_key를 우선하고, 없으면 환경변수에서 가져오기
        final_api_key = api_key or os.getenv("OPENAI_API_KEY")

        # 디버깅: API 키 상태 확인
        print(f"🔍 ConceptGeneratorAgent 초기화:")
        print(f"  - 매개변수 api_key: {'있음' if api_key else '없음'}")
        print(f"  - 환경변수 OPENAI_API_KEY: {'있음' if os.getenv('OPENAI_API_KEY') else '없음'}")
        print(f"  - 최종 final_api_key: {'있음' if final_api_key else '없음'}")
        if final_api_key:
            print(f"  - API Key 시작 부분: {final_api_key[:5]}...")

        # --- 이 부분이 중요합니다: mock_mode 설정 ---
        if not final_api_key:
            logger.warning("🎭 OpenAI API key not found for ConceptGeneratorAgent. Using mock responses.")
            print("❌ ConceptGeneratorAgent: Mock 모드로 설정됨")
            self.client = None # 실제 클라이언트 대신 None 설정
            self.mock_mode = True
        else:
            logger.info("✅ OpenAI API key found for ConceptGeneratorAgent. Initializing real OpenAI client.")
            print("✅ ConceptGeneratorAgent: 실제 API 모드로 설정됨")
            self.client = OpenAI(api_key=final_api_key)
            self.mock_mode = False
        # --- mock_mode 설정 끝 ---

        self.prompt_template = prompt_template

    def generate_concept(self, brand: str, keywords: str, campaign_type: str, style_preference: str) -> Dict[str, Any]:
        print(f"🚀 ConceptGeneratorAgent.generate_concept 호출됨 (mock_mode: {self.mock_mode})")
        
        # --- mock_mode일 경우 즉시 더미 데이터 반환 ---
        if self.mock_mode:
            logger.info("ConceptGeneratorAgent: Returning mock concept.")
            print("🎭 Mock 데이터 반환 중...")
            return {
                "scenes": [
                    {"name": "Mock Scene 1: Cozy Cafe", "duration": 10, "description": "People enjoying warm coffee in a cozy, snow-dusted cafe.", "narration": "첫눈처럼 따뜻한 스타벅스, 겨울 신메뉴와 함께."},
                    {"name": "Mock Scene 2: Product Close-up", "duration": 10, "description": "Close-up of a new starbucks winter beverage, steam rising.", "narration": "향긋한 시나몬과 부드러운 크림, 겨울의 맛을 경험하세요."},
                    {"name": "Mock Scene 3: Friends Sharing", "duration": 10, "description": "Friends laughing and sharing moments, holding Starbucks cups, by a warm fireplace.", "narration": "소중한 사람들과 함께, 스타벅스에서 당신의 겨울을 빛내세요."}
                ]
            }
        # --- mock_mode가 아닐 경우 실제 API 호출 ---
        
        print("✅ 실제 OpenAI API 호출 시작...")
        prompt = self.prompt_template.format(
            brand=brand,
            keywords=keywords,
            campaign_type=campaign_type,
            style_preference=style_preference
        )

        logger.info(f"ConceptGeneratorAgent: Sending prompt to OpenAI:\n{prompt}")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert ad copywriter. Generate a JSON-formatted three-scene storyboard. Ensure the response is valid JSON. ONLY return the JSON object, no additional text, no markdown code block."}, # JSON 형식 강제 강화
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # JSON 응답 형식 요청
            )

            content = response.choices[0].message.content
            logger.info(f"ConceptGeneratorAgent: Received raw response from OpenAI:\n{content}")

            # LLM이 JSON을 반환한다고 가정하고 파싱합니다.
            # OpenAI API가 가끔 JSON 앞에 ```json ``` 같은 마크다운을 붙일 수 있어, 이를 제거하는 로직 추가
            if content.strip().startswith("```json") and content.strip().endswith("```"):
                content = content.strip()[7:-3].strip()

            storyboard = json.loads(content)

            # 'scenes' 또는 'storyboard' 키 모두 지원
            scenes_data = None
            if "scenes" in storyboard and isinstance(storyboard["scenes"], list):
                scenes_data = storyboard["scenes"]
            elif "storyboard" in storyboard and isinstance(storyboard["storyboard"], list):
                scenes_data = storyboard["storyboard"]
                # 내부적으로 'scenes' 키로 통일
                storyboard = {"scenes": scenes_data}
            else:
                available_keys = list(storyboard.keys())
                raise ValueError(f"LLM response missing 'scenes' or 'storyboard' key, or the value is not a list. Available keys: {available_keys}. Raw content: {content}")

            print(f"✅ 파싱 성공: {len(scenes_data)}개 장면 발견")
                        
            print("✅ 실제 OpenAI API 응답 성공!")
            return storyboard

        except json.JSONDecodeError as e:
            logger.error(f"ConceptGeneratorAgent Error: Failed to parse JSON response from OpenAI: {e}")
            logger.error(f"Raw response content that caused error: {content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}. Content: {content}") from e
        except Exception as e:
            logger.error(f"ConceptGeneratorAgent Error: Failed to generate concept: {e}")
            raise

class ImageGeneratorAgent:
    """
    스토리보드 → DALL·E 3 이미지 생성기
    """
    def __init__(self, openai_api_key: Optional[str] = None, images_dir: str = "generated/images"):
        # 매개변수로 전달된 api_key를 우선하고, 없으면 환경변수에서 가져오기
        final_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # 디버깅: API 키 상태 확인
        print(f"🔍 ImageGeneratorAgent 초기화:")
        print(f"  - 매개변수 openai_api_key: {'있음' if openai_api_key else '없음'}")
        print(f"  - 환경변수 OPENAI_API_KEY: {'있음' if os.getenv('OPENAI_API_KEY') else '없음'}")
        print(f"  - 최종 final_api_key: {'있음' if final_api_key else '없음'}")
        if final_api_key:
            print(f"  - API Key 시작 부분: {final_api_key[:5]}...")

        # --- 이 부분이 중요합니다: mock_mode 설정 ---
        if not final_api_key:
            logger.warning("🎭 OpenAI API key not found for ImageGeneratorAgent. Using mock responses.")
            print("❌ ImageGeneratorAgent: Mock 모드로 설정됨")
            self.client = None
            self.mock_mode = True
        else:
            logger.info("✅ OpenAI API key found for ImageGeneratorAgent. Initializing real OpenAI client.")
            print("✅ ImageGeneratorAgent: 실제 API 모드로 설정됨")
            self.client = OpenAI(api_key=final_api_key)
            self.mock_mode = False
        # --- mock_mode 설정 끝 ---

        self.images_dir = images_dir
        os.makedirs(self.images_dir, exist_ok=True) # 폴더가 없으면 생성

    def generate_images(self, storyboard: Dict[str, Any], style_preference: str) -> List[Dict[str, Any]]:
        print(f"🚀 ImageGeneratorAgent.generate_images 호출됨 (mock_mode: {self.mock_mode})")
        
        # --- mock_mode일 경우 즉시 더미 데이터 반환 ---
        if self.mock_mode:
            logger.info("ImageGeneratorAgent: Returning mock images.")
            print("🎭 Mock 이미지 데이터 반환 중...")
            mock_images = []
            scenes = storyboard.get("scenes", [])
            for i, scene in enumerate(scenes):
                # 실제 이미지 파일은 생성되지 않고, 더미 URL만 반환
                mock_images.append({
                    "scene": scene.get("name", f"Mock Scene {i+1}"),
                    "file": None,
                    "url": f"https://via.placeholder.com/1024x1024?text=Mock+Image+{i+1}+for+{scene.get('name', 'Scene')}"
                })
            return mock_images
        # --- mock_mode가 아닐 경우 실제 API 호출 ---

        print("✅ 실제 DALL-E 3 API 호출 시작...")
        results = []
        scenes = storyboard.get("scenes", [])
        if not scenes:
            logger.warning("ImageGeneratorAgent: No scenes found in storyboard. Skipping image generation.")
            return []

        for scene in scenes:
            base_prompt = scene.get("description", "")
            prompt = f"{base_prompt}, in a {style_preference} style. High quality, detailed, realistic, suitable for advertisement."

            logger.info(f"⏳ Generating image for scene '{scene.get('name', 'Unknown')}' with prompt: {prompt}")

            try:
                resp = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    quality="standard",
                    style="vivid"
                )
                url = resp.data[0].url
                img_data = requests.get(url).content

                filename = f"{uuid.uuid4()}.png" # uuid import 필요
                path = os.path.join(self.images_dir, filename)

                with open(path, 'wb') as f:
                    f.write(img_data)

                results.append({"scene": scene.get("name", "Unknown"), "file": path, "url": url})
                logger.info(f"✅ Image generated and saved: {path}")

            except Exception as e:
                logger.error(f"❌ ImageGeneratorAgent Error: Failed to generate image for scene '{scene.get('name', 'Unknown')}': {e}")
                # 이미지 생성 실패 시 더미 URL 반환 (선택 사항)
                results.append({"scene": scene.get("name", "Unknown"), "file": None, "url": f"https://via.placeholder.com/1024x1024?text=Image+Error"})
        
        print("✅ 실제 DALL-E 3 API 호출 완료!")
        return results

# 🆕 ===== 여기서부터 새로 추가된 클래스 =====

class EnhancedAudioGeneratorAgent:
    """
    Whisper 품질 검증이 통합된 음성 생성 에이전트
    """
    def __init__(self, openai_api_key: Optional[str] = None, audio_dir: str = "generated/audio", 
                 enable_quality_validation: bool = True, max_retry_attempts: int = 2):
        final_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # 디버깅: API 키 상태 확인
        print(f"🔍 EnhancedAudioGeneratorAgent 초기화:")
        print(f"  - 매개변수 openai_api_key: {'있음' if openai_api_key else '없음'}")
        print(f"  - 환경변수 OPENAI_API_KEY: {'있음' if os.getenv('OPENAI_API_KEY') else '없음'}")
        print(f"  - 최종 final_api_key: {'있음' if final_api_key else '없음'}")
        print(f"  - 품질 검증 활성화: {enable_quality_validation}")
        print(f"  - 최대 재시도 횟수: {max_retry_attempts}")
        print(f"  - 품질 검증기 사용 가능: {QUALITY_VALIDATOR_AVAILABLE}")
        
        if final_api_key:
            print(f"  - API Key 시작 부분: {final_api_key[:5]}...")

        # Mock 모드 설정
        if not final_api_key:
            logger.warning("🎭 OpenAI API key not found for AudioGeneratorAgent. Using mock responses.")
            print("❌ AudioGeneratorAgent: Mock 모드로 설정됨")
            self.client = None
            self.mock_mode = True
        else:
            logger.info("✅ OpenAI API key found for AudioGeneratorAgent. Initializing real OpenAI client.")
            print("✅ AudioGeneratorAgent: 실제 API 모드로 설정됨")
            self.client = OpenAI(api_key=final_api_key)
            self.mock_mode = False

        self.audio_dir = audio_dir
        self.enable_quality_validation = enable_quality_validation and QUALITY_VALIDATOR_AVAILABLE
        self.max_retry_attempts = max_retry_attempts
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # 품질 검증기 초기화
        if self.enable_quality_validation and not self.mock_mode:
            try:
                self.quality_validator = AudioQualityValidator(whisper_model="base")
                print("✅ Whisper 품질 검증기 초기화 완료")
            except Exception as e:
                print(f"⚠️ Whisper 품질 검증기 초기화 실패: {e}")
                self.quality_validator = None
                self.enable_quality_validation = False
        else:
            self.quality_validator = None
            if not QUALITY_VALIDATOR_AVAILABLE:
                print("⚠️ 품질 검증기를 사용할 수 없습니다")

    def generate_narrations_with_validation(self, storyboard: Dict[str, Any], voice: str = "alloy", 
                                          min_quality_score: float = 0.8) -> List[Dict[str, Any]]:
        """
        품질 검증이 포함된 내레이션 생성
        
        Args:
            storyboard: 스토리보드 데이터
            voice: TTS 음성 옵션
            min_quality_score: 최소 품질 점수 (0.0 ~ 1.0)
            
        Returns:
            List[Dict]: 품질 검증 결과가 포함된 음성 파일 정보
        """
        print(f"🚀 EnhancedAudioGeneratorAgent.generate_narrations_with_validation 호출됨")
        print(f"  - Mock 모드: {self.mock_mode}")
        print(f"  - 품질 검증: {self.enable_quality_validation}")
        print(f"  - 최소 품질 점수: {min_quality_score}")
        
        # Mock 모드일 경우 더미 데이터 반환
        if self.mock_mode:
            return self._generate_mock_narrations_with_validation(storyboard, voice)
        
        # 실제 음성 생성 및 검증
        print("✅ 실제 OpenAI TTS + Whisper 검증 시작...")
        results = []
        scenes = storyboard.get("scenes", [])
        
        if not scenes:
            logger.warning("스토리보드에 씬이 없습니다.")
            return []

        for i, scene in enumerate(scenes):
            scene_name = scene.get("name", f"Scene {i+1}")
            narration_text = scene.get("narration", "")
            
            if not narration_text:
                logger.warning(f"씬 '{scene_name}'에 내레이션 텍스트가 없습니다.")
                continue
            
            print(f"\n🎬 씬 {i+1}/{len(scenes)} 처리 중: {scene_name}")
            
            # 품질 검증을 통한 음성 생성 (재시도 포함)
            audio_result = self._generate_audio_with_retry(
                scene_name, narration_text, voice, min_quality_score, i+1
            )
            
            results.append(audio_result)
        
        # 전체 결과 요약
        self._print_generation_summary(results)
        return results
    
    def _generate_audio_with_retry(self, scene_name: str, narration_text: str, voice: str, 
                                 min_quality_score: float, scene_number: int) -> Dict[str, Any]:
        """
        재시도 로직이 포함된 음성 생성
        """
        attempts = 0
        best_result = None
        best_score = 0.0
        
        while attempts <= self.max_retry_attempts:
            attempts += 1
            attempt_suffix = f"_attempt_{attempts}" if attempts > 1 else ""
            
            print(f"  🎤 시도 {attempts}/{self.max_retry_attempts + 1}: 음성 생성 중...")
            
            try:
                # TTS 음성 생성
                audio_result = self._generate_single_audio(
                    scene_name, narration_text, voice, scene_number, attempt_suffix
                )
                
                if not audio_result.get("file"):
                    print(f"  ❌ 시도 {attempts}: 음성 파일 생성 실패")
                    continue
                
                # 품질 검증 실행
                if self.enable_quality_validation and self.quality_validator:
                    validation_result = self.quality_validator.validate_audio_quality(
                        audio_result["file"], narration_text, min_quality_score
                    )
                    
                    audio_result["quality_validation"] = validation_result
                    current_score = validation_result.get("overall_score", 0.0)
                    
                    print(f"  📊 시도 {attempts}: 품질 점수 {current_score:.3f}")
                    
                    # 품질 검증 통과
                    if validation_result.get("passed", False):
                        print(f"  ✅ 시도 {attempts}: 품질 검증 통과!")
                        return audio_result
                    
                    # 최고 점수 결과 보관
                    if current_score > best_score:
                        best_result = audio_result
                        best_score = current_score
                        
                    print(f"  ⚠️ 시도 {attempts}: 품질 기준 미달 (점수: {current_score:.3f} < {min_quality_score})")
                    
                    # 재시도 전 잠시 대기
                    if attempts <= self.max_retry_attempts:
                        print(f"  ⏳ 재시도 전 대기 중...")
                        time.sleep(1)
                        
                else:
                    # 품질 검증 비활성화 시 바로 반환
                    print(f"  ✅ 시도 {attempts}: 품질 검증 없이 완료")
                    return audio_result
                    
            except Exception as e:
                print(f"  ❌ 시도 {attempts}: 오류 발생 - {e}")
                audio_result = {
                    "scene": scene_name,
                    "narration": narration_text,
                    "file": None,
                    "voice": voice,
                    "error": str(e),
                    "attempt": attempts
                }
        
        # 모든 시도 실패 시 최고 점수 결과 반환 (또는 오류 정보)
        if best_result:
            print(f"  🔄 모든 시도 완료: 최고 점수 결과 사용 (점수: {best_score:.3f})")
            best_result["final_attempt"] = attempts - 1
            best_result["quality_warning"] = f"품질 기준({min_quality_score})에 미달하지만 최고 점수 결과입니다."
            return best_result
        else:
            print(f"  💥 모든 시도 실패: 음성 생성 불가")
            return {
                "scene": scene_name,
                "narration": narration_text,
                "file": None,
                "voice": voice,
                "error": "모든 생성 시도 실패",
                "total_attempts": attempts - 1,
                "quality_validation": {"available": False, "passed": False}
            }
    
    def _generate_single_audio(self, scene_name: str, narration_text: str, voice: str, 
                              scene_number: int, attempt_suffix: str = "") -> Dict[str, Any]:
        """
        단일 음성 파일 생성
        """
        try:
            # OpenAI TTS API 호출
            response = self.client.audio.speech.create(
                model="tts-1",  # 또는 "tts-1-hd"
                voice=voice,
                input=narration_text,
                response_format="mp3"
            )
            
            # 파일명 생성
            safe_scene_name = "".join(c for c in scene_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"narration_{scene_number:02d}_{safe_scene_name.replace(' ', '_')}{attempt_suffix}.mp3"
            file_path = os.path.join(self.audio_dir, filename)
            
            # 음성 파일 저장
            with open(file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            return {
                "scene": scene_name,
                "narration": narration_text,
                "file": file_path,
                "duration": self._estimate_duration(narration_text),
                "voice": voice,
                "size_mb": os.path.getsize(file_path) / (1024 * 1024),
                "generated_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"음성 생성 실패: {e}")
            raise e
    
    def _generate_mock_narrations_with_validation(self, storyboard: Dict[str, Any], voice: str) -> List[Dict[str, Any]]:
        """Mock 모드용 더미 데이터 (품질 검증 결과 포함)"""
        print("🎭 Mock 오디오 데이터(품질 검증 포함) 반환 중...")
        mock_audio = []
        scenes = storyboard.get("scenes", [])
        
        for i, scene in enumerate(scenes):
            mock_audio.append({
                "scene": scene.get("name", f"Mock Scene {i+1}"),
                "narration": scene.get("narration", "Mock narration text"),
                "file": None,
                "duration": 5.0,
                "voice": voice,
                "mock_url": f"https://example.com/mock-audio-{i+1}.mp3",
                "quality_validation": {
                    "available": False,
                    "mock_mode": True,
                    "overall_score": 0.9,  # Mock 고품질 점수
                    "passed": True,
                    "message": "Mock 모드에서는 품질 검증을 수행하지 않습니다."
                }
            })
        return mock_audio
    
    def _print_generation_summary(self, results: List[Dict[str, Any]]):
        """생성 결과 요약 출력"""
        total_scenes = len(results)
        successful = len([r for r in results if r.get("file")])
        failed = total_scenes - successful
        
        print(f"\n📊 음성 생성 완료 요약:")
        print(f"  - 총 씬 수: {total_scenes}")
        print(f"  - 성공: {successful}")
        print(f"  - 실패: {failed}")
        
        if self.enable_quality_validation:
            validated = len([r for r in results if r.get("quality_validation", {}).get("available")])
            passed = len([r for r in results if r.get("quality_validation", {}).get("passed")])
            print(f"  - 품질 검증 완료: {validated}")
            print(f"  - 품질 검증 통과: {passed}")
        
        # 실패한 씬들 나열
        if failed > 0:
            print("  - 실패한 씬들:")
            for result in results:
                if not result.get("file"):
                    print(f"    • {result.get('scene', 'Unknown')}: {result.get('error', 'Unknown error')}")
    
    def _estimate_duration(self, text: str) -> float:
        """텍스트 길이 기반 재생 시간 추정"""
        if not text:
            return 0.0
        char_count = len(text)
        estimated_seconds = (char_count / 350) * 60
        return max(1.0, min(30.0, estimated_seconds))

# 🆕 ===== 새로 추가된 클래스 끝 =====