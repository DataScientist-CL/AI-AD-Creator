# offline_visualizer.py - 서버 없이 작동하는 광고 시각화
import json
from datetime import datetime

def create_sample_ad_data(brand_name="애플"):
    """샘플 광고 데이터 생성"""
    
    sample_data = {
        "task_id": "sample-task-12345",
        "status": "completed",
        "result": {
            "brand": brand_name,
            "step": "quality_complete",
            "quality_score": 100,
            "concept_success": True,
            "image_success": True,
            "voice_success": True,
            "concept": f"""
🎯 {brand_name} Advertisement Concept

Main Message: "Experience the magic of {brand_name}"

Scene Breakdown:
1. Opening (0-10s): 혁신적인 기술과 디자인이 어우러진 현대적 공간
   - 미니멀한 인테리어와 자연광
   - {brand_name} 제품들이 조화롭게 배치된 모습

2. Product Focus (10-20s): 사용자가 제품과 상호작용하는 순간
   - 직관적인 터치와 seamless한 반응
   - 사용자의 만족스러운 표정과 자연스러운 움직임

3. Closing (20-30s): 브랜드 아이덴티티 강화
   - {brand_name} 로고와 함께 "Think Different" 메시지
   - 미래를 향한 비전과 혁신적 가치 전달

Narration: "When innovation meets design, {brand_name} creates the future."

Visual Style: 
- 색상: 클린한 화이트, 소프트 그레이, 프리미엄 실버
- 조명: 자연스러운 ambient lighting
- 무드: 미래지향적이면서도 따뜻한 인간적 감성
            """,
            "images": [
                {
                    "scene": "opening scene",
                    "prompt": f"Modern minimalist space with {brand_name} products, natural lighting, clean design",
                    "file_path": "generated_opening_scene.jpg",
                    "dimensions": "1920x1080",
                    "style": "Premium, minimalist, tech-forward"
                },
                {
                    "scene": "product focus",
                    "prompt": f"Person interacting with {brand_name} device, intuitive interface, satisfied expression",
                    "file_path": "generated_product_focus.jpg", 
                    "dimensions": "1920x1080",
                    "style": "Human-centered, emotional connection"
                },
                {
                    "scene": "brand closing",
                    "prompt": f"{brand_name} logo with 'Think Different' tagline, future vision concept",
                    "file_path": "generated_brand_closing.jpg",
                    "dimensions": "1920x1080", 
                    "style": "Iconic, aspirational, brand-focused"
                }
            ],
            "voice": {
                "script": f"When innovation meets design, {brand_name} creates the future.",
                "file_path": "generated_narration.mp3",
                "duration": "30 seconds",
                "voice": "Professional, inspirational narrator",
                "tone": "Confident yet warm, forward-looking"
            }
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "request_data": {
                "brand": brand_name,
                "keywords": ["혁신", "디자인", "미래", "기술"],
                "target_audience": "20-40대 얼리어답터",
                "campaign_type": "제품 런칭",
                "style_preference": "미니멀하고 세련된"
            }
        }
    }
    
    return sample_data

def visualize_offline_ad(brand_name="애플"):
    """오프라인 광고 시각화"""
    
    print("🎬" + "="*70)
    print("🤖 AI 광고 크리에이터 - 오프라인 시각화 도구")
    print("🎬" + "="*70)
    
    # 샘플 데이터 생성
    data = create_sample_ad_data(brand_name)
    result = data["result"]
    
    print(f"\n🏷️  브랜드: {result['brand']}")
    print(f"⭐ 품질 점수: {result['quality_score']}/100")
    print(f"📅 생성 시간: {data['metadata']['created_at'][:19]}")
    print("🎬" + "="*70)
    
    # 컨셉 표시
    print("\n📝 광고 컨셉:")
    print("-" * 50)
    print(result['concept'])
    
    # 이미지 정보 표시  
    print("\n🖼️  생성된 이미지 장면:")
    print("-" * 50)
    for i, img in enumerate(result['images'], 1):
        print(f"\n{i}. 📷 {img['scene'].upper()}")
        print(f"   🎨 프롬프트: {img['prompt']}")
        print(f"   📐 크기: {img['dimensions']}")
        print(f"   🖌️  스타일: {img['style']}")
        print(f"   💾 파일: {img['file_path']}")
    
    # 음성 정보 표시
    print(f"\n🔊 음성 내레이션:")
    print("-" * 50) 
    voice = result['voice']
    print(f"📜 스크립트: \"{voice['script']}\"")
    print(f"⏱️  길이: {voice['duration']}")
    print(f"🎤 음성 톤: {voice['tone']}")
    print(f"💾 파일: {voice['file_path']}")
    
    print(f"\n🎉 {brand_name} 광고 생성 완료!")
    
    # HTML 미리보기 생성
    generate_enhanced_html(result, data['metadata'])
    
    return data

def generate_enhanced_html(result, metadata):
    """향상된 HTML 미리보기 생성"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{result['brand']} - AI 광고 크리에이터</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6; 
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 20px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.2);
                overflow: hidden;
                animation: slideUp 0.8s ease;
            }}
            
            @keyframes slideUp {{
                from {{ opacity: 0; transform: translateY(30px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .hero {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 60px 40px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .hero::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="white" opacity="0.1"/></svg>') repeat;
                animation: sparkle 20s linear infinite;
            }}
            
            @keyframes sparkle {{
                0% {{ transform: translateX(0) translateY(0); }}
                100% {{ transform: translateX(-100px) translateY(-100px); }}
            }}
            
            .hero h1 {{ 
                font-size: 3.5em; 
                margin-bottom: 20px;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                position: relative;
                z-index: 1;
            }}
            
            .hero .score {{ 
                font-size: 1.5em; 
                margin-bottom: 10px;
                background: rgba(255,255,255,0.2);
                display: inline-block;
                padding: 10px 30px;
                border-radius: 50px;
                backdrop-filter: blur(10px);
                position: relative;
                z-index: 1;
            }}
            
            .content {{ 
                padding: 50px 40px;
            }}
            
            .concept-section {{ 
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 40px; 
                margin: 40px 0;
                border-radius: 20px;
                box-shadow: 0 15px 35px rgba(240, 147, 251, 0.3);
            }}
            
            .concept-section h2 {{ 
                font-size: 2em; 
                margin-bottom: 25px;
                text-align: center;
            }}
            
            .concept-content {{ 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            
            .concept-content pre {{ 
                white-space: pre-wrap; 
                font-family: inherit;
                font-size: 1.1em;
                line-height: 1.8;
            }}
            
            .section-title {{ 
                font-size: 2.5em; 
                margin: 50px 0 30px 0;
                color: #2c3e50;
                text-align: center;
                font-weight: 700;
            }}
            
            .images-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 30px; 
                margin: 40px 0;
            }}
            
            .image-card {{ 
                background: white; 
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                border: 3px solid transparent;
            }}
            
            .image-card:hover {{ 
                transform: translateY(-10px) scale(1.02);
                box-shadow: 0 25px 50px rgba(0,0,0,0.2);
                border-color: #667eea;
            }}
            
            .image-placeholder {{ 
                width: 100%; 
                height: 280px; 
                background: linear-gradient(135deg, #667eea, #764ba2);
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: white;
                font-size: 1.2em;
                text-align: center;
                padding: 30px;
                font-weight: 600;
                position: relative;
                overflow: hidden;
            }}
            
            .image-placeholder::before {{
                content: '🎬';
                font-size: 3em;
                position: absolute;
                top: 20px;
                right: 20px;
                opacity: 0.3;
            }}
            
            .card-body {{ 
                padding: 30px;
            }}
            
            .card-title {{ 
                color: #2c3e50; 
                margin-bottom: 15px;
                font-size: 1.4em;
                font-weight: 600;
                text-transform: capitalize;
            }}
            
            .card-prompt {{ 
                color: #7f8c8d; 
                margin-bottom: 20px;
                font-style: italic;
                line-height: 1.6;
            }}
            
            .card-meta {{ 
                display: flex; 
                justify-content: space-between;
                align-items: center;
                font-size: 0.9em; 
                color: #95a5a6;
                border-top: 1px solid #ecf0f1;
                padding-top: 15px;
            }}
            
            .voice-section {{ 
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                padding: 40px; 
                margin: 40px 0;
                border-radius: 20px;
                box-shadow: 0 15px 35px rgba(79, 172, 254, 0.3);
            }}
            
            .voice-section h2 {{ 
                font-size: 2em; 
                margin-bottom: 25px;
                text-align: center;
            }}
            
            .voice-script {{ 
                background: rgba(255,255,255,0.1); 
                padding: 25px; 
                border-radius: 15px;
                font-size: 1.3em;
                font-weight: 500;
                text-align: center;
                margin: 20px 0;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            
            .voice-details {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 25px;
            }}
            
            .voice-item {{ 
                background: rgba(255,255,255,0.1); 
                padding: 20px; 
                border-radius: 15px;
                text-align: center;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            
            .voice-item strong {{ 
                display: block; 
                margin-bottom: 8px;
                font-size: 1.1em;
            }}
            
            .footer {{ 
                text-align: center; 
                padding: 40px;
                background: #2c3e50;
                color: white;
            }}
            
            .footer p {{ 
                margin: 5px 0;
                font-size: 1.1em;
            }}
            
            .badge {{ 
                display: inline-block;
                background: linear-gradient(135deg, #11998e, #38ef7d);
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-size: 0.9em;
                font-weight: 600;
                margin: 5px;
                box-shadow: 0 5px 15px rgba(17, 153, 142, 0.3);
            }}
            
            @media (max-width: 768px) {{
                .container {{ margin: 10px; }}
                .hero {{ padding: 40px 20px; }}
                .content {{ padding: 30px 20px; }}
                .hero h1 {{ font-size: 2.5em; }}
                .images-grid {{ grid-template-columns: 1fr; }}
                .section-title {{ font-size: 2em; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>🎬 {result['brand']}</h1>
                <div class="score">품질 점수 {result['quality_score']}/100 ⭐</div>
                <p>AI 광고 크리에이터로 생성된 프리미엄 광고</p>
            </div>
            
            <div class="content">
                <div class="concept-section">
                    <h2>📝 광고 컨셉</h2>
                    <div class="concept-content">
                        <pre>{result['concept']}</pre>
                    </div>
                </div>
                
                <h2 class="section-title">🖼️ 생성된 장면들</h2>
                <div class="images-grid">
    """
    
    scene_emojis = {"opening scene": "🌅", "product focus": "🎯", "brand closing": "🏆"}
    
    for i, img in enumerate(result['images']):
        emoji = scene_emojis.get(img['scene'], "🎬")
        html_content += f"""
                    <div class="image-card">
                        <div class="image-placeholder">
                            <div>
                                {emoji} {img['scene'].upper()}<br><br>
                                📐 {img['dimensions']}<br>
                                🎨 {img['style']}
                            </div>
                        </div>
                        <div class="card-body">
                            <h3 class="card-title">{emoji} {img['scene']}</h3>
                            <div class="card-prompt">
                                {img['prompt']}
                            </div>
                            <div class="card-meta">
                                <span>📁 {img['file_path']}</span>
                                <span class="badge">Ready</span>
                            </div>
                        </div>
                    </div>
        """
    
    html_content += f"""
                </div>
                
                <div class="voice-section">
                    <h2>🔊 음성 내레이션</h2>
                    <div class="voice-script">
                        "{result['voice']['script']}"
                    </div>
                    <div class="voice-details">
                        <div class="voice-item">
                            <strong>⏱️ 길이</strong>
                            {result['voice']['duration']}
                        </div>
                        <div class="voice-item">
                            <strong>🎤 음성</strong>
                            {result['voice']['voice']}
                        </div>
                        <div class="voice-item">
                            <strong>📁 파일</strong>
                            {result['voice']['file_path']}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 AI 광고 크리에이터</p>
                <p>🚀 멀티모달 AI 시스템으로 생성</p>
                <p>⭐ 프로덕션급 품질 보장</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    filename = f"{result['brand']}_광고_미리보기.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n💻 향상된 HTML 미리보기가 생성되었습니다!")
    print(f"📁 파일: {filename}")
    print("🌐 브라우저에서 이 파일을 더블클릭해서 열어보세요!")

def interactive_demo():
    """인터랙티브 데모"""
    
    print("🎬" + "="*70)
    print("🤖 AI 광고 크리에이터 - 오프라인 데모")
    print("🎬" + "="*70)
    
    print("\n어떤 브랜드의 광고를 생성해보시겠어요?")
    print("1. 애플 (Apple)")
    print("2. 삼성 (Samsung)")  
    print("3. 스타벅스 (Starbucks)")
    print("4. 나이키 (Nike)")
    print("5. 테슬라 (Tesla)")
    print("6. 직접 입력")
    
    choice = input("\n선택하세요 (1-6): ").strip()
    
    brand_map = {
        "1": "애플",
        "2": "삼성", 
        "3": "스타벅스",
        "4": "나이키",
        "5": "테슬라"
    }
    
    if choice in brand_map:
        brand = brand_map[choice]
    elif choice == "6":
        brand = input("브랜드명을 입력하세요: ").strip()
        if not brand:
            brand = "테스트브랜드"
    else:
        brand = "애플"
    
    print(f"\n🚀 {brand} 광고 생성 중...")
    visualize_offline_ad(brand)

if __name__ == "__main__":
    interactive_demo()