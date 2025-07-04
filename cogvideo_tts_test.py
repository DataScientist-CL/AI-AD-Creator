
"""
CogVideoX + TTS 통합 테스트 스크립트
DALL-E 없이 Text-to-Video + 음성 생성 테스트
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def check_system_status():
    """시스템 상태 확인"""
    print("🔍 시스템 상태 확인 중...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            services = data['services']
            video_gen = data['video_generation']
            
            print("✅ 서버 연결 성공")
            print(f"🔑 OpenAI API: {services['openai_api']}")
            print(f"🎬 CogVideoX: {services['cogvideo_text_to_video']}")  
            print(f"🎵 Whisper: {services['whisper_quality_validation']}")
            print(f"🔧 FFmpeg: {services['ffmpeg_audio_video_mixing']}")
            
            print(f"\n📊 비디오 생성 상태:")
            print(f"   CogVideoX 사용 가능: {video_gen['cogvideo_available']}")
            print(f"   CUDA 사용 가능: {video_gen['cuda_available']}")
            print(f"   GPU 메모리: {video_gen['gpu_memory_gb']:.1f}GB")
            print(f"   DALL-E 이미지: {video_gen['dall_e_images']}")
            
            # 권장사항 표시
            if not video_gen['cogvideo_available']:
                print("\n⚠️ CogVideoX가 설치되지 않았습니다!")
                print("   설치 가이드: GET /api/v1/cogvideo/status")
            
            if not video_gen['cuda_available']:
                print("\n⚠️ CUDA GPU가 감지되지 않았습니다!")
                print("   CogVideoX는 GPU가 필요합니다.")
            
            if video_gen['gpu_memory_gb'] < 6:
                print(f"\n⚠️ GPU 메모리 부족: {video_gen['gpu_memory_gb']:.1f}GB")
                print("   최소 6GB VRAM 권장")
            
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("서버가 실행 중인지 확인하세요: python main.py")
        return False

def get_cogvideo_installation_guide():
    """CogVideoX 설치 가이드 조회"""
    print("\n📦 CogVideoX 설치 상태 확인...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cogvideo/status")
        if response.status_code == 200:
            data = response.json()
            
            print(f"CogVideoX 사용 가능: {data['cogvideo_available']}")
            print(f"CUDA 사용 가능: {data['cuda_available']}")
            print(f"GPU 메모리: {data['gpu_memory']:.1f}GB")
            
            if not data['cogvideo_available']:
                print("\n🔧 설치 가이드:")
                guide = data['installation_guide']
                print(f"1. PyTorch: {guide['pytorch']}")
                print(f"2. Diffusers: {guide['diffusers']}")
                print(f"3. 비디오 유틸: {guide['video_utils']}")
                print(f"📌 {guide['note']}")
                
                print("\n⚙️ 권장 설정:")
                for quality, desc in data['recommended_settings'].items():
                    print(f"   {quality}: {desc}")
        else:
            print(f"❌ 설치 상태 확인 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 설치 상태 확인 중 오류: {e}")

def test_cogvideo_only():
    """CogVideoX 단독 테스트"""
    print("\n🧪 CogVideoX 단독 테스트")
    print("-" * 40)
    
    test_prompt = input("테스트 프롬프트를 입력하세요 (엔터시 기본값): ").strip()
    if not test_prompt:
        test_prompt = "Modern smartphone commercial advertisement with premium design and sleek aesthetics, professional cinematography"
    
    print("\n품질을 선택하세요:")
    print("1. fast (빠름, ~2분)")
    print("2. balanced (보통, ~3분)")
    print("3. high (고품질, ~5분)")
    
    quality_choice = input("선택 (1-3, 엔터시 1): ").strip()
    quality_map = {"1": "fast", "2": "balanced", "3": "high"}
    quality = quality_map.get(quality_choice, "fast")
    
    try:
        print(f"🎬 CogVideoX 테스트 시작...")
        print(f"   프롬프트: {test_prompt}")
        print(f"   품질: {quality}")
        
        response = requests.post(f"{BASE_URL}/api/v1/cogvideo/test", json={
            "prompt": test_prompt,
            "quality": quality
        })
        
        if response.status_code == 200:
            result = response.json()
            if result["test_successful"]:
                print(f"✅ CogVideoX 테스트 성공!")
                print(f"📁 비디오 경로: {result['video_path']}")
                print(f"💾 파일 크기: {result['file_size_mb']}MB")
                print(f"⚙️ 사용된 품질: {result['quality_used']}")
            else:
                print(f"❌ CogVideoX 테스트 실패: {result['message']}")
        else:
            print(f"❌ API 요청 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ CogVideoX 테스트 중 오류: {e}")

def test_full_ad_generation():
    """전체 광고 생성 테스트 (CogVideoX + TTS)"""
    print("\n🎯 전체 광고 생성 테스트")
    print("-" * 40)
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "🚗 자동차 광고 (빠른 테스트)",
            "data": {
                "brand": "현대자동차",
                "keywords": ["혁신", "스마트", "친환경", "미래"],
                "target_audience": "30-50대 자동차 구매 고객",
                "campaign_type": "신제품 출시",
                "style_preference": "모던하고 깔끔한",
                "duration": 20,
                "voice": "onyx",
                "video_quality": "fast",
                "generate_multiple_versions": False,
                "enable_image_generation": False
            }
        },
        {
            "name": "📱 스마트폰 광고 (고품질)",
            "data": {
                "brand": "갤럭시 S24",
                "keywords": ["프리미엄", "AI", "카메라", "성능", "디자인"],
                "target_audience": "20-40대 테크 얼리어답터",
                "campaign_type": "브랜드 인지도",
                "style_preference": "미니멀하고 프리미엄한",
                "duration": 30,
                "voice": "nova",
                "video_quality": "balanced",
                "generate_multiple_versions": True,
                "num_versions": 2,
                "enable_image_generation": False
            }
        },
        {
            "name": "☕ 카페 광고 (감성적)",
            "data": {
                "brand": "블루보틀 커피",
                "keywords": ["커피", "아침", "여유", "품질", "라이프스타일"],
                "target_audience": "20-30대 카페 애호가",
                "campaign_type": "브랜드 인지도",
                "style_preference": "따뜻하고 아늑한",
                "duration": 25,
                "voice": "shimmer",
                "video_quality": "balanced",
                "generate_multiple_versions": False,
                "enable_image_generation": False
            }
        },
        {
            "name": "🏢 기업 광고 (전문적)",
            "data": {
                "brand": "삼성전자",
                "keywords": ["기술", "혁신", "글로벌", "리더십", "미래"],
                "target_audience": "전문직 종사자",
                "campaign_type": "브랜드 인지도",
                "style_preference": "전문적이고 신뢰",
                "duration": 30,
                "voice": "alloy",
                "video_quality": "high",
                "generate_multiple_versions": False,
                "enable_image_generation": False
            }
        }
    ]
    
    print("테스트할 광고를 선택하세요:")
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
    print("0. 커스텀 광고 입력")
    
    choice = input("\n선택 (0-4): ").strip()
    
    if choice == "0":
        # 커스텀 입력
        brand = input("브랜드명: ").strip()
        if not brand:
            print("❌ 브랜드명은 필수입니다.")
            return
            
        keywords_input = input("키워드 (쉼표로 구분): ").strip()
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        if not keywords:
            print("❌ 최소 하나의 키워드가 필요합니다.")
            return
        
        print("\n스타일을 선택하세요:")
        styles = [
            "모던하고 깔끔한",
            "따뜻하고 아늑한", 
            "미니멀하고 프리미엄한",
            "역동적이고 에너지",
            "감성적이고 로맨틱",
            "전문적이고 신뢰"
        ]
        for i, style in enumerate(styles, 1):
            print(f"{i}. {style}")
        
        style_choice = input("선택 (1-6, 엔터시 1): ").strip()
        style_idx = int(style_choice) - 1 if style_choice.isdigit() and 1 <= int(style_choice) <= 6 else 0
        
        print("\n비디오 품질을 선택하세요:")
        print("1. fast (빠름, ~3분)")
        print("2. balanced (보통, ~5분)")
        print("3. high (고품질, ~8분)")
        
        quality_choice = input("선택 (1-3, 엔터시 1): ").strip()
        quality_map = {"1": "fast", "2": "balanced", "3": "high"}
        video_quality = quality_map.get(quality_choice, "fast")
        
        test_data = {
            "brand": brand,
            "keywords": keywords,
            "target_audience": "일반 소비자",
            "campaign_type": "브랜드 인지도",
            "style_preference": styles[style_idx],
            "duration": 30,
            "voice": "nova",
            "video_quality": video_quality,
            "generate_multiple_versions": False,
            "enable_image_generation": False
        }
        test_name = f"커스텀 ({brand})"
        
    elif choice in ["1", "2", "3", "4"]:
        idx = int(choice) - 1
        test_data = test_cases[idx]["data"]
        test_name = test_cases[idx]["name"]
    else:
        print("❌ 잘못된 선택")
        return
    
    # 광고 생성 요청
    print(f"\n🚀 {test_name} 생성 시작...")
    print(f"📋 설정:")
    print(f"   브랜드: {test_data['brand']}")
    print(f"   키워드: {', '.join(test_data['keywords'])}")
    print(f"   스타일: {test_data['style_preference']}")
    print(f"   비디오 품질: {test_data['video_quality']}")
    print(f"   음성: {test_data['voice']}")
    print(f"   길이: {test_data['duration']}초")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/ads/generate", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 작업 시작: {task_id}")
            
            # 진행 상황 모니터링
            monitor_task_progress(task_id, test_name)
        else:
            print(f"❌ 광고 생성 요청 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"오류 내용: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"응답 내용: {response.text}")
                
    except Exception as e:
        print(f"❌ 광고 생성 요청 중 오류: {e}")

def monitor_task_progress(task_id: str, test_name: str):
    """작업 진행 상황 모니터링"""
    print(f"\n📊 {test_name} 진행 상황 모니터링")
    print(f"작업 ID: {task_id}")
    print("-" * 60)
    
    start_time = time.time()
    last_progress = 0
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/ads/status/{task_id}")
            if response.status_code == 200:
                status = response.json()
                progress = status["progress"]
                current_step = status["current_step"]
                task_status = status["status"]
                
                if progress != last_progress:
                    elapsed = int(time.time() - start_time)
                    print(f"[{elapsed:3d}초] [{progress:3d}%] {current_step}")
                    last_progress = progress
                
                if task_status == "completed":
                    print(f"\n🎉 {test_name} 생성 완료!")
                    show_results(task_id)
                    break
                    
                elif task_status == "failed":
                    print(f"\n❌ {test_name} 생성 실패:")
                    print(f"오류: {status.get('error', '알 수 없는 오류')}")
                    
                    # 상세 오류 정보가 있으면 표시
                    if status.get('error_details'):
                        print(f"상세 정보: {status['error_details'][:200]}...")
                    break
                    
            else:
                print(f"❌ 상태 확인 실패: {response.status_code}")
                break
                    
            time.sleep(3)  # 3초마다 상태 확인
            
        except KeyboardInterrupt:
            print(f"\n⏹️ 사용자에 의해 모니터링 중단")
            print(f"작업 ID {task_id}는 백그라운드에서 계속 실행됩니다.")
            break
        except Exception as e:
            print(f"❌ 상태 확인 중 오류: {e}")
            break

def show_results(task_id: str):
    """결과 표시"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ads/result/{task_id}")
        if response.status_code == 200:
            result = response.json()
            metadata = result["result"]["metadata"]
            content = result["result"]["content"]
            
            print(f"\n📋 생성 결과 요약:")
            print(f"   📺 총 비디오 수: {metadata['total_videos']}")
            print(f"   🎵 음성 파일 수: {metadata['total_audio_files']}")
            print(f"   🖼️ 이미지 수: {metadata['total_images']}")
            print(f"   ⚡ 비디오 품질: {metadata['video_quality']}")
            print(f"   🤖 CogVideoX 사용: {metadata['cogvideo_used']}")
            print(f"   💰 DALL-E 사용: {metadata['dall_e_used']}")
            print(f"   🔄 다중 버전: {metadata['multiple_versions']}")
            
            # 파일 경로들 표시
            if content.get("final_videos"):
                print(f"\n📁 생성된 최종 비디오:")
                for i, video_path in enumerate(content["final_videos"], 1):
                    print(f"   {i}. {video_path}")
            
            if content.get("generated_videos"):
                print(f"\n🎬 원본 CogVideoX 비디오:")
                for i, video_path in enumerate(content["generated_videos"], 1):
                    print(f"   {i}. {video_path}")
            
            if content.get("validated_audio"):
                print(f"\n🎵 생성된 음성 파일:")
                for i, audio in enumerate(content["validated_audio"], 1):
                    if audio and audio.get("file"):
                        quality_info = audio.get("quality_validation", {})
                        score = quality_info.get("overall_score", "N/A")
                        print(f"   {i}. {audio['file']} (품질점수: {score})")
            
            # 품질 리포트
            quality_report = content.get("quality_report", {})
            if quality_report:
                print(f"\n📊 품질 리포트:")
                print(f"   생성 성공: {quality_report.get('generation_successful', 'N/A')}")
                print(f"   비디오 품질: {quality_report.get('video_quality', 'N/A')}")
                
                audio_quality = quality_report.get('audio_quality', {})
                if audio_quality:
                    print(f"   음성 품질 검증: {audio_quality.get('available', 'N/A')}")
                    if audio_quality.get('overall_score'):
                        print(f"   음성 품질 점수: {audio_quality['overall_score']}")
            
        else:
            print(f"❌ 결과 조회 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"오류: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 결과 표시 중 오류: {e}")

def list_recent_tasks():
    """최근 작업 목록 조회"""
    print("\n📋 최근 작업 목록 조회")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tasks?limit=10")
        if response.status_code == 200:
            data = response.json()
            tasks = data["tasks"]
            
            if not tasks:
                print("생성된 작업이 없습니다.")
                return
            
            print(f"총 {data['total']}개 작업 중 최근 {len(tasks)}개:")
            print("-" * 80)
            print(f"{'작업ID':<10} {'상태':<10} {'진행률':<8} {'생성시간':<20} {'브랜드':<15}")
            print("-" * 80)
            
            for task in tasks:
                task_id = task["task_id"][:8]
                status = task["status"]
                progress = f"{task['progress']}%"
                created_at = task["created_at"][:19].replace("T", " ")
                brand = task.get("request_data", {}).get("brand", "N/A")[:14]
                
                print(f"{task_id:<10} {status:<10} {progress:<8} {created_at:<20} {brand:<15}")
            
            # 특정 작업 결과 조회 옵션
            task_id_input = input("\n결과를 볼 작업 ID를 입력하세요 (엔터시 건너뛰기): ").strip()
            if task_id_input:
                # 전체 작업 ID 찾기
                full_task_id = None
                for task in tasks:
                    if task["task_id"].startswith(task_id_input):
                        full_task_id = task["task_id"]
                        break
                
                if full_task_id:
                    if task["status"] == "completed":
                        show_results(full_task_id)
                    else:
                        print(f"작업 상태: {task['status']} ({task['progress']}%)")
                        print(f"현재 단계: {task['current_step']}")
                else:
                    print("❌ 해당 작업 ID를 찾을 수 없습니다.")
        else:
            print(f"❌ 작업 목록 조회 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 작업 목록 조회 중 오류: {e}")

def main():
    """메인 함수"""
    print("🎬 CogVideoX + TTS 광고 생성 테스트")
    print("=" * 60)
    
    # 시스템 상태 확인
    if not check_system_status():
        print("\n❌ 시스템 상태 확인 실패.")
        print("1. 서버가 실행 중인지 확인: python main.py")
        print("2. OpenAI API 키가 설정되었는지 확인")
        print("3. CogVideoX가 설치되었는지 확인")
        
        choice = input("\n그래도 계속하시겠습니까? (y/N): ").strip().lower()
        if choice != 'y':
            return
    
    while True:
        print("\n🎯 테스트 메뉴:")
        print("1. CogVideoX 단독 테스트")
        print("2. 전체 광고 생성 테스트 (CogVideoX + TTS)")
        print("3. 시스템 상태 재확인")
        print("4. CogVideoX 설치 가이드")
        print("5. 최근 작업 목록 조회")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-5): ").strip()
        
        if choice == "0":
            print("👋 테스트를 종료합니다.")
            break
        elif choice == "1":
            test_cogvideo_only()
        elif choice == "2":
            test_full_ad_generation()
        elif choice == "3":
            check_system_status()
        elif choice == "4":
            get_cogvideo_installation_guide()
        elif choice == "5":
            list_recent_tasks()
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()