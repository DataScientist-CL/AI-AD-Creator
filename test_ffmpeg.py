# test_ffmpeg.py - 간단한 FFmpeg 테스트
import subprocess
import sys
import os

def test_ffmpeg():
    print("🔍 FFmpeg 설치 확인 중...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg 설치됨!")
            version = result.stdout.split('\n')[0]
            print(f"   버전: {version}")
            return True
        else:
            print("❌ FFmpeg 실행 실패")
            return False
    except Exception as e:
        print(f"❌ FFmpeg 테스트 실패: {e}")
        return False

def test_simple_video():
    print("\n🎬 간단한 비디오 생성 테스트...")
    
    try:
        # 테스트 이미지 생성 (3초간)
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', 'color=c=blue:size=640x480:duration=3',
            '-c:v', 'libx264', '-t', '3',
            'test_video.mp4'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists('test_video.mp4'):
            file_size = os.path.getsize('test_video.mp4')
            print(f"✅ 테스트 비디오 생성 성공! (크기: {file_size} bytes)")
            
            # 테스트 파일 삭제
            os.remove('test_video.mp4')
            print("✅ 테스트 파일 정리 완료")
            return True
        else:
            print(f"❌ 비디오 생성 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 비디오 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🎬 AI 광고 크리에이터 - FFmpeg 테스트")
    print("=" * 50)
    
    ffmpeg_ok = test_ffmpeg()
    video_ok = test_simple_video()
    
    if ffmpeg_ok and video_ok:
        print("\n🎉 모든 테스트 통과! AI 광고 크리에이터 준비 완료!")
        print("\n🚀 서버 실행:")
        print("python main.py")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 확인해주세요.")