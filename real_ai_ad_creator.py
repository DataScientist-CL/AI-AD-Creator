import os
import openai
import requests
import webbrowser
from datetime import datetime
from io import BytesIO
from PIL import Image

# Optional: ElevenLabs for voice
try:
    from elevenlabs.client import ElevenLabs
    HAS_ELEVEN = True
except ImportError:
    HAS_ELEVEN = False

# Folder setup
generated_dir = os.path.join(os.getcwd(), 'generated')
images_dir = os.path.join(generated_dir, 'images')
audio_dir = os.path.join(generated_dir, 'audio')
for d in (generated_dir, images_dir, audio_dir):
    os.makedirs(d, exist_ok=True)

class RealAIAdCreator:
    def __init__(self):
        # Load or prompt for API keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY') or input('OpenAI API Key: ').strip()
        openai.api_key = self.openai_api_key

        # Setup ElevenLabs client
        if HAS_ELEVEN:
            self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY') or input('ElevenLabs API Key (press Enter to skip): ').strip()
            if self.elevenlabs_api_key:
                self.eleven_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            else:
                self.eleven_client = None
        else:
            self.eleven_client = None

    def generate_images(self, brand_name, scenes):
        results = []
        for idx, scene in enumerate(scenes, 1):
            prompt = scene['prompt']
            print(f"⏳ Generating image {idx}/{len(scenes)}: {prompt}")
            resp = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            url = resp.data[0].url
            img_data = requests.get(url).content
            filename = f"{brand_name.lower()}_{idx}.png"
            path = os.path.join(images_dir, filename)
            with open(path, 'wb') as f:
                f.write(img_data)
            results.append({'scene': scene['name'], 'file': path})
        return results


def generate_voice(self, script, brand_name):
    if not getattr(self, 'eleven_client', None):
        print("⚠️ ElevenLabs not configured or missing key, skipping voice generation.")
        return None

    print("⏳ Generating voice narration...")
    response = self.eleven_client.text_to_speech.convert(
        voice_id="Anna Kim",
        text=script,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )
    filename = f"{brand_name.lower()}_narration.mp3"
    path = os.path.join(audio_dir, filename)
    with open(path, 'wb') as f:
        for chunk in response:
            f.write(chunk)
    return path



    def build_html(self, brand_name, images, voice_path):
        timestamp = datetime.utcnow().isoformat()
        html_path = os.path.join(generated_dir, f"{brand_name}_ad_preview.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><head><meta charset='utf-8'><title>{brand_name} Ad Preview</title></head><body>\n")
            f.write(f"<h1>{brand_name} Advertisement</h1>\n<p>Generated: {timestamp}</p>\n<hr>\n")
            for img in images:
                f.write(f"<h2>{img['scene']}</h2><img src='../generated/images/{os.path.basename(img['file'])}' style='max-width:100%;'><br>\n")
            if voice_path:
                f.write(f"<h2>Voice Narration</h2><audio controls src='../generated/audio/{os.path.basename(voice_path)}'></audio>\n")
            f.write("</body></html>")
        return html_path

    def run(self):
        brands = {
            '1': ('Apple', [
                {'name': 'Opening', 'prompt': 'Minimalist modern space with Apple products, natural light'},
                {'name': 'Product Focus', 'prompt': 'User interacting with sleek Apple device'},
                {'name': 'Closing', 'prompt': 'Apple logo with Think Different tagline'}
            ]),
            '2': ('Samsung', [
                {'name': 'Opening', 'prompt': 'Futuristic showcase of Samsung Galaxy devices, neon accents'},
                {'name': 'Product Focus', 'prompt': 'Hands using Samsung touchscreen interface'},
                {'name': 'Closing', 'prompt': 'Samsung logo with Next is Now tagline'}
            ]),
            '3': ('Starbucks', [
                {'name': 'Opening', 'prompt': 'Cozy cafe interior with warm lighting, steaming coffee cups'},
                {'name': 'Product Focus', 'prompt': 'Barista pouring latte art for customer'},
                {'name': 'Closing', 'prompt': 'Starbucks logo with Inspire Connection tagline'}
            ]),
            '4': ('Nike', [
                {'name': 'Opening', 'prompt': 'Athlete tying Nike shoes in dynamic stadium setting'},
                {'name': 'Product Focus', 'prompt': 'Close-up of Nike shoe in motion'},
                {'name': 'Closing', 'prompt': 'Nike swoosh with Just Do It tagline'}
            ]),
            '5': ('Tesla', [
                {'name': 'Opening', 'prompt': 'Sleek Tesla electric car in urban environment at dawn'},
                {'name': 'Product Focus', 'prompt': 'Driver enjoying silent ride in Tesla interior'},
                {'name': 'Closing', 'prompt': 'Tesla logo with Drive the Future tagline'}
            ])
        }
        print("Which brand ad would you like to generate?")
        for key, (name, _) in brands.items():
            print(f"{key}. {name}")
        choice = input("Select (1-5): ").strip()
        if choice not in brands:
            print("Invalid choice, exiting.")
            return
        brand_name, scenes = brands[choice]
        images = self.generate_images(brand_name, scenes)
        voice_scripts = {
            "Apple": "When innovation meets design, Apple creates the future.",
            "Samsung": "Next is Now. Samsung Galaxy brings tomorrow to you today.",
            "Starbucks": "Every cup tells a story. Starbucks, inspire connection.",
            "Nike": "Just Do It. Empower your inner athlete with Nike.",
            "Tesla": "Drive the future. Tesla, sustainable innovation in motion."
        }
        script = voice_scripts.get(brand_name, f"When innovation meets design, {brand_name} creates the future.")
        voice = self.generate_voice(script, brand_name)
        html = self.build_html(brand_name, images, voice)
        print(f"🎉 Ad generated! Opening preview: {html}")
        webbrowser.open(f"file:///{html}")

if __name__ == '__main__':
    creator = RealAIAdCreator()
    creator.run()