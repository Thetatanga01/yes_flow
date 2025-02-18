import os
import shutil

from crewai.tools import BaseTool
from elevenlabs import ElevenLabs
from pydantic import Field, BaseModel
from pydub import AudioSegment

from util.LanguageUtil import LanguageUtil


class TextToSpeechToolInput(BaseModel):
    input_text: str = Field(..., description="Texts to convert to speech")
    save_path: str = Field(..., description="Path to save the audio files")
    language: str = Field(..., description="Language ")
    combined: str = Field(default="false", description="Whether to combine audio files")


class TextToSpeechTool(BaseTool):
    name: str = "text_to_speech_tool"
    description: str = "Converts text to speech using the ElevenLabs API."
    args_schema = TextToSpeechToolInput

    def _run(self, input_text: str, save_path: str, language: str, combined: str = "false") -> dict:
        # save_path'deki fazladan tırnakları kaldır
        save_path = save_path.strip('"')
        voice_id = LanguageUtil().get_voice_id(language)

        # Ses dosyalarını temizle ve klasör oluştur
        shutil.rmtree(save_path, ignore_errors=True)
        os.makedirs(save_path, exist_ok=True)

        client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))

        # combined değeri string olduğu için boolean'a dönüştür
        is_combined = combined.lower() == "true"
        combined_audio = None if is_combined else []
        temp_audio_files = []

        # input_text'i `|` ile bölerek bir liste oluştur
        text_list = input_text.split("|")

        print("Text-to-speech işlemi başladı.")
        for i, text in enumerate(text_list):
            text = text.strip()  # Metin başındaki ve sonundaki boşlukları temizle
            if not text:  # Boş metin varsa atla
                continue

            try:

                print(f"{text} metni {voice_id} voice_id'si ile ses dosyasına dönüştürülüyor...")
                # Ses oluşturma
                audio_generator = client.text_to_speech.convert(
                    text=text,
                    voice_id=LanguageUtil().get_voice_id(language),
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128",
                    voice_settings={
                        "stability": 0.9,
                        "similarity_boost": 0.9,
                        "style": 0.2,
                        "use_speaker_boost": False
                    },
                    apply_text_normalization="auto"
                )

                # Geçici ses dosyasını yaz
                temp_audio_file = os.path.join(save_path, f"{i}.mp3")
                temp_audio_files.append(temp_audio_file)

                # Dosya yazma
                with open(temp_audio_file, "wb") as f:
                    for chunk in audio_generator:
                        f.write(chunk)

                print(f"Temp audio dosyası {temp_audio_file} oluşturuldu...")

                # Ses dosyasını yükle ve birleştir
                if is_combined:
                    audio_segment = AudioSegment.from_file(temp_audio_file, format="mp3")
                    if combined_audio is None:
                        combined_audio = audio_segment
                    else:
                        combined_audio += AudioSegment.silent(duration=1000) + audio_segment

            finally:
                # `audio_generator` kaynağını kapat
                if hasattr(audio_generator, "close"):
                    audio_generator.close()

        # Eğer birleştirme isteniyorsa, combined.mp3 olarak kaydet
        if is_combined and combined_audio is not None:
            combined_file_path = os.path.join(save_path, "combined.mp3")
            combined_audio.export(combined_file_path, format="mp3")
            print(f"Birleştirilmiş ses dosyası {combined_file_path} oluşturuldu.")

        full_path = os.path.join(save_path, "combined.mp3")
        return {"status": "success", "combined_audio": full_path, "temp_audio_files": temp_audio_files}
