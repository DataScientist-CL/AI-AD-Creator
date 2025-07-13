# quick_test.py - 빠른 Whisper 품질 검증 테스트

import requests
import json
import time

def test_health():
    """헬스체크 테스트"""
    print("🏥 헬스체크 테스트...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ 서버 상태: 정상")
            
            # 품질 검증 상태 확인
            quality_val = data.get("quality_validation", {})
            whisper_available = quality_val.get("whisper_available", False)
            librosa_available = quality_val.get("librosa_available", False)
            
            print(f"📊 Whisper 사용 가능: {'✅' if whisper_available else '❌'}")
            print(f"📊 Librosa 사용 가능: {'✅' if librosa_available else '❌'}")
            print(f"📊 지원 모델: {quality_val.get('supported_whisper_models', [])}")
            
            return whisper_available
        else:
            print(f"❌ 헬스체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 헬스체크 오류: {e}")
        return False

def test_quality_settings():
    """품질 검증 설정 테스트"""
    print("\n⚙️ 품질 검증 설정 테스트...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/quality/settings")
        if response.status_code == 200:
            settings = response.json()
            print("✅ 설정 조회 성공")
            print(f"📋 Whisper 사용 가능: {settings.get('whisper_available', False)}")
            print(f"📋 기본 설정: {json.dumps(settings.get('default_settings', {}), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 설정 조회 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 설정 조회 오류: {e}")
        return False

def test_quality_validation():
    """품질 검증 직접 테스트"""
    print("\n🧪 품질 검증 직접 테스트...")
    
    test_texts = [
        "안녕하세요. 스타벅스의 새로운 겨울 메뉴를 소개합니다.",
        "따뜻한 커피로 당신의 하루를 시작하세요.",
        "품질이 우수한 원두로 만든 특별한 음료입니다."
    ]
    
    success_count = 0
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n🎤 테스트 {i}/3: {test_text[:30]}...")
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/v1/quality/test",
                params={"test_text": test_text}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('test_successful', False):
                    print(f"✅ 테스트 성공!")
                    test_result = result.get('test_result', {})
                    print(f"  - 음성 생성: {'✅' if test_result.get('audio_generated') else '❌'}")
                    print(f"  - 품질 검증: {'✅' if test_result.get('quality_validated') else '❌'}")
                    print(f"  - 품질 점수: {test_result.get('quality_score', 0):.3f}")
                    success_count += 1
                else:
                    print(f"❌ 테스트 실패: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ 테스트 실패: HTTP {response.status_code}")
                print(f"   응답: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
    
    print(f"\n📊 테스트 결과: {success_count}/{len(test_texts)} 성공")
    return success_count > 0

def test_mini_ad_generation():
    """간단한 광고 생성 테스트"""
    print("\n🎬 간단한 광고 생성 테스트...")
    
    test_request = {
        "brand": "테스트 브랜드",
        "keywords": ["품질", "테스트"],
        "target_audience": "테스트 사용자",
        "duration": 15,  # 짧은 시간
        "voice": "alloy",
        "enable_quality_validation": True,
        "min_quality_score": 0.6,  # 낮은 임계값
        "max_retry_attempts": 1     # 적은 재시도
    }
    
    try:
        # 광고 생성 요청
        print("📝 광고 생성 요청 중...")
        response = requests.post(
            "http://127.0.0.1:8000/api/v1/ads/generate",
            json=test_request,
            timeout=10
        )
        
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id")
            print(f"✅ 작업 시작: {task_id}")
            
            # 상태 확인 (최대 1분 대기)
            print("⏳ 작업 상태 확인 중...")
            max_attempts = 12  # 1분 (5초 × 12)
            
            for attempt in range(max_attempts):
                time.sleep(5)
                
                try:
                    status_response = requests.get(
                        f"http://127.0.0.1:8000/api/v1/ads/status/{task_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        progress = status_data.get('progress', 0)
                        step = status_data.get('current_step', 'Unknown')
                        status = status_data.get('status', 'unknown')
                        
                        print(f"📊 진행률: {progress}% - {step}")
                        
                        if status == "completed":
                            print("✅ 광고 생성 완료!")
                            
                            # 결과 조회
                            result_response = requests.get(
                                f"http://127.0.0.1:8000/api/v1/ads/result/{task_id}",
                                timeout=10
                            )
                            
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                content = result_data.get("result", {}).get("content", {})
                                
                                # 품질 리포트 확인
                                if "quality_report" in content:
                                    quality_report = content["quality_report"]
                                    summary = quality_report.get("summary", {})
                                    print(f"📊 품질 리포트:")
                                    print(f"  - 총 파일: {summary.get('total_files', 0)}")
                                    print(f"  - 성공률: {summary.get('successful_files', 0)}/{summary.get('total_files', 0)}")
                                    print(f"  - 품질 통과율: {summary.get('quality_pass_rate', 0)}%")
                                    print(f"  - 평균 품질 점수: {summary.get('average_quality_score', 0):.3f}")
                                
                                return True
                            else:
                                print(f"❌ 결과 조회 실패: {result_response.status_code}")
                            break
                            
                        elif status == "failed":
                            print(f"❌ 작업 실패: {status_data.get('error', 'Unknown error')}")
                            break
                    else:
                        print(f"❌ 상태 조회 실패: {status_response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"⏰ 상태 조회 타임아웃 (시도 {attempt + 1}/{max_attempts})")
                except Exception as e:
                    print(f"❌ 상태 조회 오류: {e}")
            
            print("⏰ 테스트 시간 초과 또는 완료")
            return False
        else:
            print(f"❌ 광고 생성 요청 실패: {response.status_code}")
            print(f"   응답: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 광고 생성 요청 타임아웃")
        return False
    except Exception as e:
        print(f"❌ 광고 생성 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 Whisper 품질 검증 시스템 빠른 테스트")
    print("=" * 60)
    
    # 1. 헬스체크
    whisper_available = test_health()
    
    if not whisper_available:
        print("\n⚠️ Whisper를 사용할 수 없습니다.")
        print("   하지만 Mock 모드로 테스트를 계속 진행합니다.")
    
    # 2. 설정 확인
    test_quality_settings()
    
    # 3. 품질 검증 테스트
    quality_test_success = test_quality_validation()
    
    # 4. 간단한 광고 생성 테스트 (선택적)
    print(f"\n{'='*60}")
    print("🎬 간단한 광고 생성 테스트를 실행하시겠습니까?")
    print("   (약 30초-1분 소요, Mock 모드에서도 테스트 가능)")
    
    user_input = input("실행하려면 'y'를 입력하세요 (기본값: n): ").strip().lower()
    
    if user_input == 'y':
        ad_test_success = test_mini_ad_generation()
    else:
        print("⏭️ 광고 생성 테스트 건너뛰기")
        ad_test_success = None
    
    # 최종 결과
    print(f"\n{'='*60}")
    print("🎉 테스트 완료!")
    print(f"📊 Whisper 사용 가능: {'✅' if whisper_available else '❌'}")
    print(f"📊 품질 검증 테스트: {'✅' if quality_test_success else '❌'}")
    if ad_test_success is not None:
        print(f"📊 광고 생성 테스트: {'✅' if ad_test_success else '❌'}")
    
    if whisper_available and quality_test_success:
        print("\n🎊 축하합니다! Whisper 품질 검증 시스템이 정상 작동합니다!")
    elif quality_test_success:
        print("\n✅ Mock 모드에서 시스템이 정상 작동합니다!")
        print("   Whisper 설치 후 실제 품질 검증을 사용할 수 있습니다.")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 로그를 확인해보세요.")

if __name__ == "__main__":
    main()