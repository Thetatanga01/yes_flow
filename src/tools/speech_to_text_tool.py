import os
import shutil

import whisper
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()


class SpeechToTextTool(BaseTool):
    name: str = "speech to text tool"
    description: str = "Converts speech to text using the Whisper Ai model."

    def _run(self, audio_files: list, language_code: str, save_path: str, language: str) -> dict:
        print("LanguageCode: " + language_code)

        # Klasörü temizle ve yeniden oluştur
        shutil.rmtree(save_path, ignore_errors=True)
        os.makedirs(save_path, exist_ok=True)

        print("Ses dosyaları yükleniyor:", audio_files)
        print("Zaman çizelgelerinin çıkarılacağı path:", save_path)

        # Whisper modelini yükle
        print("Whisper modelini yükle")
        model = whisper.load_model("large", device="cpu")

        # Her ses dosyasını işle ve ayrı dosyalara yaz
        timelines = []  # Her dosyanın sonuçlarını tutmak için
        for idx, audio_file in enumerate(audio_files):
            print(f"Ses dosyasını işliyor: {audio_file}")

            # Ses dosyasını transkribe et
            print("Ses dosyası transkribe ediliyor")
            result = model.transcribe(audio_file, language=language_code)

            # Zaman çizelgesini oluştur
            print("Segmentler zaman çizelgesine ekleniyor")
            timeline = []
            for segment in result['segments']:
                start_time = segment['start']  # Segmentin başlangıç zamanı
                end_time = segment['end']  # Segmentin bitiş zamanı
                text = segment['text'].strip()  # Segment metni
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
    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async functionality is not implemented yet.")
