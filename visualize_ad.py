# visualize_ad.py - 광고 시각화 도구
import requests
import json

def visualize_ad_result(task_id):
    """광고 결과를 시각적으로 표시"""
    
    # API에서 결과 가져오기
    response = requests.get(f"http://localhost:8000/api/v1/ads/result/{task_id}")
    
    if response.status_code == 200:
        data = response.json()
        result = data["result"]
        
        print("🎬" + "="*60)
        print(f"🏷️  브랜드: {result['brand']}")
        print(f"⭐ 품질 점수: {result['quality_score']}/100")
        print("🎬" + "="*60)
        
        # 컨셉 표시
        print("\n📝 광고 컨셉:")
        print("-" * 40)
        print(result['concept'])
        
        # 이미지 정보 표시
        print("\n🖼️  생성된 이미지:")
        print("-" * 40)
        for i, img in enumerate(result['images'], 1):
            print(f"{i}. {img['scene'].upper()}")
            print(f"   📐 크기: {img['dimensions']}")
            print(f"   🎨 프롬프트: {img['prompt']}")
            print(f"   💾 파일: {img['file_path']}")
            print()
        
        # 음성 정보 표시
        print("🔊 음성 정보:")
        print("-" * 40)
        voice = result['voice']
        print(f"📜 스크립트: {voice['script']}")
        print(f"⏱️  길이: {voice['duration']}")
        print(f"🎤 음성: {voice['voice']}")
        
        print("\n🎉 광고 생성 완료!")
        
        # 웹에서 보기 위한 HTML 생성
        generate_html_preview(result)
        
    else:
        print(f"❌ 결과를 가져올 수 없습니다: {response.status_code}")

def generate_html_preview(result):
    """HTML 미리보기 생성"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{result['brand']} 광고 미리보기</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 20px; border-radius: 10px; }}
            .concept {{ background: #f8f9fa; padding: 20px; margin: 20px 0; 
                       border-radius: 10px; border-left: 5px solid #007bff; }}
            .image-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); 
                          gap: 20px; margin: 20px 0; }}
            .image-card {{ background: white; padding: 20px; border-radius: 10px; 
                          box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
            .placeholder {{ width: 100%; height: 200px; background: #e9ecef; 
                           border-radius: 5px; display: flex; align-items: center; 
                           justify-content: center; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎬 {result['brand']} 광고</h1>
            <p>품질 점수: {result['quality_score']}/100 ⭐</p>
        </div>
        
        <div class="concept">
            <h2>📝 광고 컨셉</h2>
            <pre>{result['concept']}</pre>
        </div>
        
        <h2>🖼️ 생성된 장면들</h2>
        <div class="image-grid">
    """
    
    for img in result['images']:
        html_content += f"""
            <div class="image-card">
                <div class="placeholder">
                    {img['scene'].upper()}<br>
                    📐 {img['dimensions']}
                </div>
                <h3>{img['scene']}</h3>
                <p><strong>프롬프트:</strong> {img['prompt']}</p>
            </div>
        """
    
    html_content += f"""
        </div>
        
        <div class="concept">
            <h2>🔊 음성 내레이션</h2>
            <p><strong>스크립트:</strong> {result['voice']['script']}</p>
            <p><strong>길이:</strong> {result['voice']['duration']}</p>
            <p><strong>음성:</strong> {result['voice']['voice']}</p>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #6c757d;">
            <p>🤖 AI 광고 크리에이터로 생성됨</p>
        </footer>
    </body>
    </html>
    """
    
    # HTML 파일 저장
    with open("ad_preview.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("💻 HTML 미리보기가 생성되었습니다!")
    print("📁 파일: ad_preview.html")
    print("🌐 브라우저에서 이 파일을 열어보세요!")

if __name__ == "__main__":
    # 최근 task_id 입력 (여기에 실제 ID 입력)
    task_id = input("Task ID를 입력하세요: ")
    visualize_ad_result(task_id)