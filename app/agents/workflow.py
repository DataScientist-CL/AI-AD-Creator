# app/agents/workflow.py
import os
import sys
import time
from typing import Dict, Any, List
from urllib.parse import quote


from dotenv import load_dotenv
load_dotenv()   # 현재 디렉토리의 .env 파일을 자동으로 로드


# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from langgraph.graph import Graph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("⚠️ LangGraph not available, using simple workflow")
    LANGGRAPH_AVAILABLE = False

from app.core.mock_openai_client import MockOpenAIClient

class AdCreatorWorkflow:
    """AI 광고 생성 워크플로우 - LangGraph 기반"""

    def __init__(self):
        self.client = MockOpenAIClient()
        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_langgraph_workflow()
        print("✅ AdCreatorWorkflow initialized")

    def _build_langgraph_workflow(self):
        """LangGraph 워크플로우 구축"""
        if not LANGGRAPH_AVAILABLE:
            return None

        workflow = Graph()

        # 노드 추가
        workflow.add_node("concept_generator", self.generate_concept_node)
        workflow.add_node("image_generator", self.generate_image_node)
        workflow.add_node("voice_generator", self.generate_voice_node)
        workflow.add_node("quality_checker", self.check_quality_node)

        # 엣지 정의 (선형 플로우)
        workflow.add_edge("concept_generator", "image_generator")
        workflow.add_edge("image_generator", "voice_generator")
        workflow.add_edge("voice_generator", "quality_checker")

        # 조건부 엣지 (품질 체크 후)
        workflow.add_conditional_edges(
            "quality_checker",
            self.should_retry,
            {
                "retry": "concept_generator",
                "complete": END
            }
        )

        # 시작점 설정
        workflow.set_entry_point("concept_generator")

        return workflow.compile()

    def generate_concept_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """광고 컨셉 생성 노드"""
        print("🎨 [Node] Concept Generation Started")

        brand = state.get("brand", "Unknown Brand")
        keywords = state.get("keywords", "premium, quality")

        try:
            concept = self.client.generate_concept(brand, keywords)
            state["concept"] = concept
            state["step"] = "concept_complete"
            state["concept_success"] = True

            print("✅ [Node] Concept Generation Complete")
            return state

        except Exception as e:
            print(f"❌ [Node] Concept Generation Failed: {str(e)}")
            state["error"] = f"Concept generation failed: {str(e)}"
            state["concept_success"] = False
            return state


    def generate_image_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 생성 노드"""
        print("🖼️ [Node] Image Generation Started")

        if not state.get("concept_success", False):
            print("⚠️ [Node] Skipping image generation - no concept")
            return state

        try:
            # 3개의 이미지 프롬프트 생성 시뮬레이션
            images = []
            scenes = ["opening scene", "product focus", "brand closing"]

            for i, scene in enumerate(scenes):
                print(f"🎨 Generating image {i+1}/3: {scene}")
                time.sleep(0.5)  # 시뮬레이션 딜레이

                # URL-safe 인코딩 (한글 포함 가능)
                encoded_text = quote(scene, safe='')  # 공백 포함 모든 문자 인코딩

                images.append({
                    "scene": scene,
                    "url": f"https://placeholder.com/800x600?text={encoded_text}"
                })

            state["images"] = images
            state["step"] = "images_complete"
            state["image_success"] = True

            print(f"✅ [Node] Generated {len(images)} images")
            return state

        except Exception as e:
            print(f"❌ [Node] Image Generation Failed: {str(e)}")
            state["error"] = f"Image generation failed: {str(e)}"
            state["image_success"] = False
            return state


    def generate_voice_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """음성 생성 노드"""
        print("🔊 [Node] Voice Generation Started")

        if not state.get("image_success", False):
            print("⚠️ [Node] Skipping voice generation - no images")
            return state

        try:
            brand = state.get("brand", "Unknown Brand")

            # 내레이션 스크립트 생성
            narration_script = f"Experience the magic of {brand}. Where quality meets comfort."

            print("🎙️ Generating narration audio...")
            time.sleep(1)  # 시뮬레이션 딜레이

            state["narration"] = {
                "script": narration_script,
                "audio_url": "https://placeholder.com/audio.mp3",
                "duration": 25  # seconds
            }
            state["step"] = "voice_complete"
            state["voice_success"] = True

            print("✅ [Node] Voice Generation Complete")
            return state

        except Exception as e:
            print(f"❌ [Node] Voice Generation Failed: {str(e)}")
            state["error"] = f"Voice generation failed: {str(e)}"
            state["voice_success"] = False
            return state

    def check_quality_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """품질 체크 노드"""
        print("🔍 [Node] Quality Check Started")

        quality_score = 0
        quality_issues = []

        # 각 단계별 품질 점수 계산
        if state.get("concept_success", False):
            quality_score += 30
        else:
            quality_issues.append("Concept generation failed")

        if state.get("image_success", False):
            quality_score += 30
        else:
            quality_issues.append("Image generation failed")

        if state.get("voice_success", False):
            quality_score += 30
        else:
            quality_issues.append("Voice generation failed")

        # 전체적인 완성도 점수
        if quality_score >= 80:
            quality_score += 10

        state["quality_score"] = quality_score
        state["quality_issues"] = quality_issues
        state["step"] = "quality_complete"

        print(f"📊 [Node] Quality Score: {quality_score}/100")
        if quality_issues:
            print(f"🚨 Quality Issues: {', '.join(quality_issues)}")

        return state

    def should_retry(self, state: Dict[str, Any]) -> str:
        """재시도 여부 결정"""
        quality_score = state.get("quality_score", 0)
        retry_count = state.get("retry_count", 0)

        if quality_score < 70 and retry_count < 2:
            state["retry_count"] = retry_count + 1
            print(f"🔄 Quality insufficient, retrying ({retry_count + 1}/2)")
            return "retry"
        else:
            print("✅ Workflow complete")
            return "complete"

    def simple_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 워크플로우 (LangGraph 없이)"""
        print("🔄 Running simple workflow...")

        state = {**input_data, "retry_count": 0}

        # 순차적 실행
        state = self.generate_concept_node(state)
        state = self.generate_image_node(state)
        state = self.generate_voice_node(state)
        state = self.check_quality_node(state)

        return state

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        print("🚀 AI Advertisement Creation Workflow Started")
        print("=" * 50)

        initial_state = {
            **input_data,
            "retry_count": 0,
            "step": "starting"
        }

        try:
            if LANGGRAPH_AVAILABLE and self.graph:
                # LangGraph 워크플로우 실행
                print("🔗 Using LangGraph workflow")
                final_state = self.graph.invoke(initial_state)
            else:
                # 간단한 워크플로우 실행
                print("📝 Using simple workflow")
                final_state = self.simple_process(initial_state)

            print(f"\n🎉 Workflow Complete!")
            print(f"📊 Final Quality Score: {final_state.get('quality_score', 0)}/100")

            print(f"• Brand: {final_state.get('brand')}")
            print(f"• Step: {final_state.get('step')}")
            print(f"• Quality Score: {final_state.get('quality_score', 0)}/100")
            print(f"• Concept: {'✅' if final_state.get('concept_success') else '❌'}")
            print(f"• Images: {'✅' if final_state.get('image_success') else '❌'}")
            print(f"• Voice: {'✅' if final_state.get('voice_success') else '❌'}")

            if final_state.get("images"):
                print(f"• Generated {len(final_state['images'])} images")

            return final_state

        except Exception as e:
            print(f"💥 Workflow Failed: {str(e)}")
            return {
                **initial_state,
                "error": f"Workflow execution failed: {str(e)}",
                "step": "failed"
            }

def test_workflow():
    """워크플로우 테스트"""
    print("🧪 AI Advertisement Workflow Test")
    print("=" * 40)

    workflow = AdCreatorWorkflow()

    test_input = {
        "brand": "Starbucks",
        "keywords": "winter menu, cozy, warmth, holiday",
        "duration": 30,
        "target_audience": "coffee lovers"
    }

    print(f"\n📋 Input: {test_input}")
    print("\n" + "="*50)

    result = workflow.process(test_input)

    print("\n" + "="*50)
    print("📋 Final Result Summary:")
    print(f"• Brand: {result.get('brand')}")
    print(f"• Step: {result.get('step')}")
    print(f"• Quality Score: {result.get('quality_score', 0)}/100")
    print(f"• Concept: {'✅' if result.get('concept_success') else '❌'}")
    print(f"• Images: {'✅' if result.get('image_success') else '❌'}")
    print(f"• Voice: {'✅' if result.get('voice_success') else '❌'}")

    if result.get("images"):
        print(f"• Generated {len(result['images'])} images")

    return result

if __name__ == "__main__":
    test_workflow()