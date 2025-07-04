
"""
Complete AI Ad Creator 통합 테스트 스크립트
브랜드 + 키워드 → 완성된 광고 영상 (CogVideoX + TTS + BGM)
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def check_system_status():
    """시스템 상태 및 준비도 확인"""
    print("🔍 Complete AI Ad Creator 시스템 상태 확인...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            services = data['services']
            capabilities = data['capabilities']
            
            print(f"\n 핵심 서비스 상태:")
            print(f"   🔑 OpenAI TTS: {services.get('openai_api', 'N/A')}") # 오류 방지를 위해 .get() 사용
            print(f"   🎬 CogVideoX: {services.get('cogvideo_text_to_video', 'N/A')}")
            print(f"   🎼 Riffusion BGM: {services.get('riffusion_bgm', 'N/A')}")
            print(f"   🔧 FFmpeg: {services.get('ffmpeg_video_composition', 'N/A')}")
            
            print(f"\n 시스템 준비도:")
            print(f"   완전 워크플로우: {'✅ 준비' if capabilities['complete_workflow'] else '❌ 미준비'}")
            print(f"   영상 생성: {'✅' if capabilities['video_generation'] else '❌'}")
            print(f"   음성 생성: {'✅' if capabilities['voice_generation'] else '❌'}")
            print(f"   BGM 생성: {'✅' if capabilities['bgm_generation'] else '❌'}")
            print(f"   비디오 합성: {'✅' if capabilities['video_composition'] else '❌'}")
            
            if not capabilities['complete_workflow']:
                print(f"\n⚠️ 일부 기능이 준비되지 않았습니다!")
                if not capabilities['video_generation']:
                    print("   - CogVideoX 설치 필요")
                if not capabilities['voice_generation']:
                    print("   - OpenAI API 키 설정 필요")
                if not capabilities['video_composition']:
                    print("   - FFmpeg 설치 필요")
                return False
            
            print(f"\n 현재 활동: {data['active_tasks']}개 작업 진행 중")
            return True
            
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("💡 서버를 먼저 실행하세요: python main.py")
        return False

def test_complete_ad_generation():
    """완전한 광고 생성 테스트"""
    print("\n🎬 완전한 광고 영상 생성 테스트")
    print("=" * 60)
    
    # 미리 준비된 테스트 케이스들
    test_cases = [
        {
            "name": "스타벅스 겨울 신메뉴 (빠른 테스트)",
            "data": {
                "brand": "스타벅스",
                "keywords": "겨울 신메뉴, 따뜻한 커피, 아늑한 카페 분위기, 크리스마스 시즌",
                "target_audience": "20-30대 커피 애호가",
                "style_preference": "따뜻하고 아늑한",
                "duration": 20,
                "video_quality": "fast",
                "voice": "nova",
                "enable_bgm": True,
                "bgm_style": "warm"
            }
        },
        {
            "name": "현대자동차 신모델 (고품질)",
            "data": {
                "brand": "현대자동차",
                "keywords": "혁신적인 전기차, 친환경 기술, 미래의 이동수단, 스마트 기능",
                "target_audience": "30-50대 자동차 구매 고객",
                "style_preference": "모던하고 깔끔한",
                "duration": 30,
                "video_quality": "balanced",
                "voice": "onyx",
                "enable_bgm": True,
                "bgm_style": "professional"
            }
        },
        {
            "name": "애플 아이폰 프로 (프리미엄)",
            "data": {
                "brand": "Apple iPhone",
                "keywords": "프로급 카메라, 혁신적인 디자인, 프리미엄 성능, 창의적인 도구",
                "target_audience": "테크 얼리어답터",
                "style_preference": "미니멀하고 프리미엄한",
                "duration": 30,
                "video_quality": "high",
                "voice": "alloy",
                "enable_bgm": True,
                "bgm_style": "minimal"
            }
        },
        {
            "name": "나이키 운동화 (에너제틱)",
            "data": {
                "brand": "Nike",
                "keywords": "달리기의 자유, 한계를 뛰어넘는 도전, 운동의 즐거움, 승리의 순간",
                "target_audience": "운동을 즐기는 모든 사람",
                "style_preference": "역동적이고 에너지",
                "duration": 25,
                "video_quality": "balanced",
                "voice": "echo",
                "enable_bgm": True,
                "bgm_style": "energetic"
            }
        }
    ]
    
    print("테스트할 광고를 선택하세요:")
    for i, case in enumerate(test_cases, 1):
        duration_text = f"{case['data']['duration']}초"
        quality_text = case['data']['video_quality']
        print(f"{i}. {case['name']} ({duration_text}, {quality_text})")
    print("0. 커스텀 광고 직접 입력")
    
    choice = input("\n선택 (0-4): ").strip()
    
    if choice == "0":
        # 커스텀 입력
        print("\n✨ 커스텀 광고 생성")
        brand = input("브랜드명: ").strip()
        if not brand:
            print("❌ 브랜드명은 필수입니다.")
            return
            
        keywords = input("키워드/컨셉 (자유롭게 입력): ").strip()
        if not keywords:
            print("❌ 키워드는 필수입니다.")
            return
        
        target_audience = input("타겟 고객 (엔터시 기본값): ").strip() or "일반 소비자"
        
        print("\n스타일을 선택하세요:")
        styles = [
            "모던하고 깔끔한", "따뜻하고 아늑한", "미니멀하고 프리미엄한",
            "역동적이고 에너지", "감성적이고 로맨틱", "전문적이고 신뢰"
        ]
        for i, style in enumerate(styles, 1):
            print(f"{i}. {style}")
        
        style_choice = input("선택 (1-6, 엔터시 1): ").strip()
        style_idx = int(style_choice) - 1 if style_choice.isdigit() and 1 <= int(style_choice) <= 6 else 0
        
        print("\n품질을 선택하세요:")
        print("1. fast (빠름, ~5분)")
        print("2. balanced (보통, ~8분)")  
        print("3. high (고품질, ~12분)")
        
        quality_choice = input("선택 (1-3, 엔터시 1): ").strip()
        quality_map = {"1": "fast", "2": "balanced", "3": "high"}
        video_quality = quality_map.get(quality_choice, "fast")
        
        duration = input("영상 길이 (15-60초, 엔터시 30): ").strip()
        try:
            duration = int(duration) if duration else 30
            duration = max(15, min(60, duration))
        except:
            duration = 30
        
        test_data = {
            "brand": brand,
            "keywords": keywords,
            "target_audience": target_audience,
            "style_preference": styles[style_idx],
            "duration": duration,
            "video_quality": video_quality,
            "voice": "nova",
            "enable_bgm": True,
            "bgm_style": "auto"
        }
        test_name = f"커스텀 ({brand})"
        
    elif choice in ["1", "2", "3", "4"]:
        idx = int(choice) - 1
        test_data = test_cases[idx]["data"]
        test_name = test_cases[idx]["name"]
    else:
        print("❌ 잘못된 선택")
        return
    
    # 예상 소요 시간 안내
    quality_times = {"fast": "약 5분", "balanced": "약 8분", "high": "약 12분"}
    expected_time = quality_times.get(test_data["video_quality"], "약 8분")
    
    print(f"\n {test_name} 생성 시작...")
    print(f" 설정 요약:")
    print(f"   브랜드: {test_data['brand']}")
    print(f"   키워드: {test_data['keywords']}")
    print(f"   스타일: {test_data['style_preference']}")
    print(f"   길이: {test_data['duration']}초")
    print(f"   품질: {test_data['video_quality']} ({expected_time} 예상)")
    print(f"   음성: {test_data['voice']}")
    print(f"   BGM: {'포함' if test_data['enable_bgm'] else '미포함'}")
    
    confirm = input(f"\n계속하시겠습니까? (y/N): ").strip().lower()
    if confirm != 'y':
        print("취소되었습니다.")
        return
    
    # 광고 생성 요청
    try:
        print(f"\n API 요청 전송 중...")
        response = requests.post(f"{BASE_URL}/api/v1/ads/create-complete", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f" 작업 시작: {task_id}")
            
            # 진행 상황 모니터링
            monitor_complete_ad_progress(task_id, test_name, expected_time)
        else:
            print(f"❌ 광고 생성 요청 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"오류 내용: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"응답 내용: {response.text}")
                
    except Exception as e:
        print(f"❌ 광고 생성 요청 중 오류: {e}")

def monitor_complete_ad_progress(task_id: str, test_name: str, expected_time: str):
    """완전 광고 생성 진행 상황 모니터링"""
    print(f"\n {test_name} 진행 상황 모니터링")
    print(f"작업 ID: {task_id}")
    print(f"예상 소요 시간: {expected_time}")
    print("-" * 70)
    
    start_time = time.time()
    last_progress = 0
    
    # 진행 단계별 설명
    stage_descriptions = {
        0: " 준비 중",
        10: " GPT-4로 광고 컨셉 생성 중",
        20: " OpenAI TTS 나레이션 생성 중", 
        35: " CogVideoX AI 영상 생성 중 (가장 오래 걸림)",
        65: " Riffusion BGM 생성 중",
        80: " FFmpeg로 최종 영상 합성 중",
        95: " 품질 검사 및 정리 중",
        100: " 완료!"
    }
    
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
                    elapsed_str = f"{elapsed//60:02d}:{elapsed%60:02d}"
                    
                    # 현재 단계 설명 추가
                    stage_desc = ""
                    for stage_progress, desc in stage_descriptions.items():
                        if progress >= stage_progress:
                            stage_desc = desc
                    
                    print(f"[{elapsed_str}] [{progress:3d}%] {stage_desc}")
                    print(f"         └─ {current_step}")
                    last_progress = progress
                
                if task_status == "completed":
                    elapsed = int(time.time() - start_time)
                    elapsed_str = f"{elapsed//60:02d}:{elapsed%60:02d}"
                    print(f"\n🎉 {test_name} 생성 완료! (총 소요시간: {elapsed_str})")
                    show_complete_results(task_id)
                    break
                    
                elif task_status == "failed":
                    print(f"\n❌ {test_name} 생성 실패:")
                    print(f"오류: {status.get('error', '알 수 없는 오류')}")
                    
                    if status.get('error_details'):
                        print(f"상세 정보: {status['error_details'][:200]}...")
                    break
                    
            else:
                print(f"❌ 상태 확인 실패: {response.status_code}")
                break
                    
            time.sleep(5)  # 5초마다 상태 확인
            
        except KeyboardInterrupt:
            print(f"\n⏹️ 사용자에 의해 모니터링 중단")
            print(f"작업 ID {task_id}는 백그라운드에서 계속 실행됩니다.")
            print(f"나중에 확인하려면: GET /api/v1/ads/result/{task_id}")
            break
        except Exception as e:
            print(f"❌ 상태 확인 중 오류: {e}")
            break

def show_complete_results(task_id: str):
    """완전 광고 생성 결과 표시"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ads/result/{task_id}")
        if response.status_code == 200:
            result = response.json()
            content = result["result"]["content"]
            metadata = result["result"]["metadata"]
            
            print(f"\n🎬 광고 영상 생성 결과")
            print("=" * 50)
            print(f"🏢 브랜드: {content['brand']}")
            print(f"📁 파일 크기: {metadata['file_size_mb']}MB")
            print(f"⏱️ 길이: {metadata['duration']}초")
            print(f"🎨 스타일: {metadata['style']}")
            print(f"📹 품질: {metadata['video_quality']}")
            print(f"🎵 음성: {metadata['voice_used']}")
            print(f"🎼 BGM: {'포함' if metadata['bgm_included'] else '미포함'}")
            
            print(f"\n📝 생성된 나레이션:")
            print(f'"{content["narration_text"]}"')
            
            print(f"\n📁 생성된 파일들:")
            if content.get("final_video"):
                print(f"   🎬 최종 광고 영상: {content['final_video']}")
            if content.get("narration_audio"):
                print(f"   🎵 나레이션 음성: {content['narration_audio']}")
            if content.get("original_video"):
                print(f"   📹 원본 영상: {content['original_video']}")
            if content.get("bgm_audio"):
                print(f"   🎼 배경음악: {content['bgm_audio']}")
            
            print(f"\n💾 다운로드:")
            print(f"   웹 다운로드: {BASE_URL}/download/{task_id}")
            print(f"   직접 경로: {content.get('final_video', 'N/A')}")
            
        else:
            print(f"❌ 결과 조회 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"오류: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 결과 표시 중 오류: {e}")

def list_recent_complete_ads():
    """최근 생성된 완전 광고 목록 조회"""
    print("\n📋 최근 생성된 광고 목록")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tasks?limit=10")
        if response.status_code == 200:
            data = response.json()
            tasks = data["tasks"]
            
            if not tasks:
                print("생성된 광고가 없습니다.")
                return
            
            print(f"총 {data['total']}개 작업 중 최근 {len(tasks)}개:")
            print("-" * 90)
            print(f"{'ID':<8} {'브랜드':<15} {'상태':<10} {'진행률':<8} {'생성시간':<20}")
            print("-" * 90)
            
            for task in tasks:
                task_id = task["task_id"][:8]
                brand = task.get("request_data", {}).get("brand", "N/A")[:14]
                status = task["status"]
                progress = f"{task['progress']}%"
                created_at = task["created_at"][:19].replace("T", " ")
                
                print(f"{task_id:<8} {brand:<15} {status:<10} {progress:<8} {created_at:<20}")
            
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
                        show_complete_results(full_task_id)
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
    print("🎬 Complete AI Ad Creator 통합 테스트")
    print("=" * 60)
    print("브랜드 + 키워드 → 완성된 광고 영상 (CogVideoX + TTS + BGM)")
    print("=" * 60)
    
    # 시스템 상태 확인
    if not check_system_status():
        print("\n❌ 시스템이 준비되지 않았습니다.")
        print("💡 해결 방법:")
        print("1. 서버 실행: python main.py")
        print("2. OpenAI API 키 설정 확인")
        print("3. CogVideoX 설치 확인")
        print("4. FFmpeg 설치 확인")
        
        choice = input("\n그래도 계속하시겠습니까? (y/N): ").strip().lower()
        if choice != 'y':
            return
    
    while True:
        print("\n🎯 테스트 메뉴:")
        print("1. 완전 광고 영상 생성 테스트")
        print("2. 시스템 상태 재확인")
        print("3. 최근 생성된 광고 목록 조회")
        print("4. 웹 인터페이스 열기 (브라우저)")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-4): ").strip()
        
        if choice == "0":
            print("👋 테스트를 종료합니다.")
            break
        elif choice == "1":
            test_complete_ad_generation()
        elif choice == "2":
            check_system_status()
        elif choice == "3":
            list_recent_complete_ads()
        elif choice == "4":
            import webbrowser
            print(f"🌐 웹 브라우저에서 {BASE_URL} 열기...")
            webbrowser.open(BASE_URL)
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()