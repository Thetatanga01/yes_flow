import os
import re
import shutil

from crewai.tools import BaseTool
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import Field, BaseModel

load_dotenv()


class SpeechToTextToolInput(BaseModel):
    audio_files_folder_path: str = Field(..., description="Audio files to be used in the video")
    language_code: str = Field(..., description="Language code for the audio files")
    save_path: str = Field(..., description="Path to save the timelines")


class SpeechToTextTool(BaseTool):
    name: str = "speech to text tool"
    description: str = "Converts speech to text using the Whisper Ai model."
    args_schema = SpeechToTextToolInput

    def _run(self, audio_files_folder_path: str, language_code: str, save_path: str) -> dict:
        try:
            client = OpenAI()
            print("LanguageCode: " + language_code)
            print("audio_files_folder_path:", audio_files_folder_path)
            print("Zaman çizelgelerinin çıkarılacağı path:", save_path)
            print("path:", os.path.join(os.getcwd(), audio_files_folder_path))

            audio_files = sorted(
                [os.path.join(audio_files_folder_path, f) for f in os.listdir(audio_files_folder_path) if
                 re.match(r'.*\.mp3$', f)],
                key=lambda x: [int(num) if num.isdigit() else num for num in re.split(r'(\d+)', os.path.basename(x))]
            )

            print("Ses dosyaları:", audio_files)

            # Klasörü temizle ve yeniden oluştur
            shutil.rmtree(save_path, ignore_errors=True)
            os.makedirs(save_path, exist_ok=True)

            # Her ses dosyasını işle ve ayrı dosyalara yaz
            timelines = []  # Her dosyanın sonuçlarını tutmak için
            for idx, audio_file in enumerate(audio_files):
                print("---------------------------------")
                print(f"Ses dosyasını işliyor: {audio_file}")

                # Ses dosyasını OpenAI Whisper API ile transkribe et
                print("Ses dosyası transkribe ediliyor")
                with open(audio_file, "rb") as audio:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language=language_code,
                        response_format="verbose_json"  # Segment bilgilerini almak için
                    )

                # Zaman çizelgesini oluştur
                print("Segmentler zaman çizelgesine ekleniyor")
                timeline = []
                for segment in response.segments:
                    start_time = segment.start  # Segmentin başlangıç zamanı
                    end_time = segment.end  # Segmentin bitiş zamanı
                    text = segment.text.strip()  # Segment metni
                    timeline.append((start_time, end_time, text))

                # Zaman çizelgesini bir dosyaya yaz
                output_timeline = os.path.join(save_path, f"{idx}.txt")
                print(f"Zaman çizelgesi {output_timeline} dosyasına yazılıyor")
                with open(output_timeline, 'w', encoding='utf-8') as file:
                    for start, end, text in timeline:
                        file.write(f"{start:.2f} - {end:.2f}: {text}\n")

                timelines.append(output_timeline)

            print(f"Tüm zaman çizelgeleri {save_path} klasörüne kaydedildi.")
            return {"audio_files": audio_files, "timelines": timelines}
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return {"error": str(e)}

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async functionality is not implemented yet.")
