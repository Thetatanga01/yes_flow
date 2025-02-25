import glob
import os
import random
import re
import shutil
import subprocess
import textwrap
import time
from typing import List, Dict

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field, BaseModel

from util.DimensionUtil import Provider, DimensionType

load_dotenv()


class VideoGeneratorToolInput(BaseModel):
    audio_files_folder_path: str = Field(..., description="Audio files to be used in the video")
    timeline_files_folder_path: str = Field(..., description="Text files containing timeline data")
    source_folder: str = Field(..., description="Videos or pictures using as background")
    save_path: str = Field(..., description="Path to save the video")
    combined: str = Field("true", description="Combine all videos in the save_path")


class VideoGeneratorTool(BaseTool):
    name: str = "video_generator_tool"
    description: str = "Converts given audio, images and text to a video"
    args_schema = VideoGeneratorToolInput

    def _run(self,
             audio_files_folder_path: str,
             timeline_files_folder_path: str,
             source_folder: str,
             save_path: str,
             combined: str = "true") -> dict:

        print("audio_files_folder_path", audio_files_folder_path)
        print("timeline_files_folder_path", timeline_files_folder_path)
        print("source_folder", source_folder)
        print("save_path", save_path)
        print("current dimension", DimensionType.get_default().get(Provider.VIDEO))
        print("combined", combined)

        shutil.rmtree(save_path, ignore_errors=True)
        os.makedirs(save_path, exist_ok=True)

        # videoda kullanilacak text dosyalari
        timelines = sorted(
            [os.path.join(timeline_files_folder_path, f) for f in os.listdir(timeline_files_folder_path) if
             f.endswith(".txt")],
            key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()) if re.search(r'\d+',
                                                                                           os.path.basename(x)) else x
        ) if os.path.exists(timeline_files_folder_path) else []

        # videoda kullanilacak ses dosyalari
        audio_files = sorted(
            [os.path.join(audio_files_folder_path, f) for f in os.listdir(audio_files_folder_path) if
             f.endswith(".mp3")],
            key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()) if re.search(r'\d+',
                                                                                           os.path.basename(x)) else x
        ) if os.path.exists(audio_files_folder_path) else []

        # if source_folder contains "video" then generate video from videos otherwise generate video from images
        if source_folder.find("video") != -1:
            return self.generate_video_from_videos(audio_files, timelines,
                                                   source_folder,
                                                   save_path,
                                                   combined)
        else:
            return self.generate_video_from_images(audio_files, timelines,
                                                   source_folder,
                                                   save_path, combined)

    def generate_video_from_images(self, audio_files: list[str], timelines: list[str],
                                   source_folder: str, save_path: str,
                                   combined: str) -> dict:

        # find the pictures in source_folder by sorted order like 0.png 1.png 2.png .... 10.png 11.png
        picture_files = sorted(
            [os.path.join(source_folder, f) for f in os.listdir(source_folder) if
             f.endswith(".png") or f.endswith(".jpg")],
            key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()) if re.search(r'\d+',
                                                                                           os.path.basename(x)) else x
        )

        # Arka plan resmi bulunamazsa hata fırlat
        if not picture_files:
            raise ValueError(f"{source_folder} klasöründe png veya jpg dosyası bulunamadı")

        results = {}

        # Her ses dosyası için video oluştur, i adinda bir degisken ile index degerini al
        for index, (audio_path, timeline_path) in enumerate(zip(audio_files, timelines)):
            try:
                timeline_data = self.parse_timeline(timeline_path)

                filename = os.path.basename(audio_path)
                output_filename = f"{os.path.splitext(filename)[0]}.mp4"
                output_path = os.path.join(save_path, output_filename)

                background_picture = picture_files[index]
                audio_duration = self.get_audio_duration(audio_path)

                command = self.ffmpeg_for_using_pictures(
                    background_picture=background_picture,
                    audio_path=audio_path,
                    output_path=output_path,
                    duration=audio_duration,
                    timeline=timeline_data
                )

                # FFmpeg komutunu çalıştır ve çıktıyı yakala
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if process.returncode != 0:
                    raise RuntimeError(f"FFmpeg hatası: {process.stderr}")

                results[audio_path] = {
                    "status": "success",
                    "output_path": output_path
                }

            except Exception as e:
                results[audio_path] = {
                    "status": "error",
                    "error": str(e)
                }

        if combined == "true":
            self.combine_videos(save_path)

        return results

    def wrap_text_with_newlines(self, text, width):
        """Metni belirtilen genişlikte satırlara böl ve FFmpeg için formatla"""
        # Metni satırlara böl
        lines = textwrap.fill(text, width=width).split('\n')

        # Her satır için y pozisyonunu hesapla
        total_lines = len(lines)
        line_height = 70  # Satırlar arası yükseklik
        start_y = f"(h-{total_lines}*{line_height})/2"  # Dikey ortalama

        # Her satır için ayrı drawtext filtresi oluştur
        drawtext_commands = []
        # fontfile = "/System/Library/Fonts/SFArabic.ttf"

        for i, line in enumerate(lines):
            # FFmpeg için özel karakterleri escape et
            line = line.replace("'", "\\'").replace('"', '\\"')
            line = line.replace("'", "\\""")
            y_position = f"{start_y}+{i}*{line_height}"  # Her satır için y pozisyonu

            command = (
                f"drawtext=text='{line}':"
                f"fontsize=60:fontcolor=white:"
                f"box=1:boxcolor=black@0.5:boxborderw=10:"  # Siyah arka plan ve kenar kalınlığı
                f"x=(w-text_w)/2:y={y_position}"
            )
            drawtext_commands.append(command)

        return drawtext_commands

    # below methods belong to the video making from videos
    def generate_video_from_videos(self, audio_files: list[str], timelines: list[str],
                                   source_folder: str,
                                   save_path: str, combined: str) -> dict:

        video_files = glob.glob(os.path.join(source_folder, "*.mp4"))
        if not video_files:
            raise ValueError(f"Video klasöründe MP4 dosyası bulunamadı: {source_folder}")

        results = {}

        for audio_path, timeline_path in zip(audio_files, timelines):
            try:
                timeline_data = self.parse_timeline(timeline_path)

                filename = os.path.basename(audio_path)
                output_filename = f"{os.path.splitext(filename)[0]}.mp4"
                output_path = os.path.join(save_path, output_filename)

                background_video = random.choice(video_files)
                audio_duration = self.get_audio_duration(audio_path)

                command = self.ffmpeg_for_using_videos(
                    background_video=background_video,
                    audio_path=audio_path,
                    output_path=output_path,
                    duration=audio_duration,
                    timeline=timeline_data
                )

                # FFmpeg komutunu çalıştır ve çıktıyı yakala
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if process.returncode != 0:
                    raise RuntimeError(f"FFmpeg hatası: {process.stderr}")

                results[audio_path] = {
                    "status": "success",
                    "output_path": output_path
                }

            except Exception as e:
                results[audio_path] = {
                    "status": "error",
                    "error": str(e)
                }

        if combined == "true":
            self.combine_videos(save_path)

        return results

    def combine_videos(self, save_path: str) -> dict:
        try:
            # Dizindeki tüm mp4 dosyalarını bul
            video_files = [f for f in os.listdir(save_path) if f.endswith('.mp4')]

            if not video_files:
                return {"status": "error", "message": "Dizinde MP4 dosyası bulunamadı"}

            # Dosyaları numerik sıraya göre sırala
            video_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

            # Geçici bir dosya listesi oluştur
            temp_file_path = os.path.join(save_path, "file_list.txt")
            with open(temp_file_path, "w") as f:
                for video in video_files:
                    f.write(f"file '{video}'\n")

            # Birleştirilmiş dosya için çıktı yolu
            output_path = os.path.join(save_path, "combined_output.mp4")

            # ffmpeg komutu
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_file_path,
                '-c', 'copy',
                output_path
            ]

            # ffmpeg'i çalıştır
            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Geçici dosyayı sil
            os.remove(temp_file_path)
            shutil.copy2(f"{save_path}/combined_output.mp4", f"output/done/{str(int(time.time()))}.mp4")

            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Videolar başarıyla birleştirildi",
                    "output_path": output_path
                }
            else:
                return {
                    "status": "error",
                    "message": f"FFmpeg hatası: {process.stderr}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Hata oluştu: {str(e)}"
            }

    def parse_timeline(self, timeline_path: str) -> List[Dict]:
        """Text dosyasından timeline verilerini okur."""
        timeline_data = []
        with open(timeline_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    time_part, text = line.split(':', 1)
                    start_time, end_time = time_part.split('-')

                    start_time = float(start_time.strip())
                    end_time = float(end_time.strip())
                    text = text.strip()

                    timeline_data.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": text
                    })
                except Exception as e:
                    raise ValueError(f"Satır parse edilemedi: {line} - Hata: {str(e)}")

        return timeline_data

    def get_audio_duration(self, audio_path: str) -> float:
        """Ses dosyasının süresini FFmpeg ile alır"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())

    def find_with(self, width: str) -> int:
        """Metni belirtilen genişlikte satırlara böl ve FFmpeg için formatla"""
        if width == "1920":
            return 60
        else:
            return 35

    def ffmpeg_for_using_videos(self, background_video: str, audio_path: str,
                                output_path: str, duration: float, timeline: List[Dict]) -> List[str]:

        (width, height) = DimensionType.get_default().get(Provider.VIDEO)
        """FFmpeg komutunu hazırlar"""
        command = [
            'ffmpeg',
            '-stream_loop', '-1',  # Video döngüsü
            '-i', background_video,  # Arka plan videosu
            '-i', audio_path,  # Ses dosyası
            '-t', str(duration)  # Çıkış süresi (ses uzunluğu kadar)
        ]

        # Text overlay filtrelerini hazırla
        drawtext_filters = []
        for entry in timeline:
            # Metni multiline formatına çevir
            multiline_text_commands = self.wrap_text_with_newlines(entry['text'], self.find_with(width))
            for text_command in multiline_text_commands:
                drawtext_filters.append(
                    f"{text_command}:enable='between(t,{entry['start_time']},{entry['end_time']})'"
                )

        filter_complex = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:-1:-1,setsar=1,fps=30[bg];"
            f"[bg]{','.join(drawtext_filters)}[outv]"
        )

        # Video filtrelerini oluştur (horizontal videolar için dönüştürme dahil)
        # Komuta filtreleri ve output ayarlarını ekle
        command.extend([
            '-filter_complex', filter_complex,
            '-map', '[outv]',  # Filtrelenmiş videoyu çıkışa ekle
            '-map', '1:a',  # Ses dosyasını çıkışa ekle
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Orta hız/kalite dengesi
            '-c:a', 'aac',  # Ses codec
            '-shortest',  # Çıkışı en kısa medya dosyasına göre kes
            '-y',  # Üzerine yazma
            output_path
        ])

        return command



    #for images
    def ffmpeg_for_using_pictures(self, background_picture: str, audio_path: str,
                                  output_path: str, duration: float, timeline: List[Dict]) -> \
            List[str]:

        (width, height) = DimensionType.get_default().get(Provider.VIDEO)

        """PNG dosyalarından video oluşturmak için FFmpeg komutunu hazırlar"""
        command = [
            'ffmpeg',
            '-loop', '1',  # PNG dosyasını sabit bir görüntü olarak loop yap
            '-framerate', '30',  # Videonun FPS değeri
            '-i', background_picture,  # Arka plan PNG dosyası
            '-i', audio_path,  # Ses dosyası
            '-t', str(duration),  # Çıkış süresi (ses uzunluğu kadar)
        ]

        # Text overlay filtrelerini hazırla
        drawtext_filters = []
        for entry in timeline:
            # Metni multiline formatına çevir
            multiline_text_commands = self.wrap_text_with_newlines(entry['text'], self.find_with(width))
            for text_command in multiline_text_commands:
                drawtext_filters.append(
                    f"{text_command}:enable='between(t,{entry['start_time']},{entry['end_time']})'"
                )

        # Zoompan filtresini ekleyin
        # zoompan'ın d parametresini duration'a göre ayarla
        # d = (duration * fps) / zoompan'ın kare sayısı
        fps = 30  # FFmpeg'de belirtilen framerate
        zoompan_duration = int(duration * fps)  # Toplam kare sayısı

        zoompan_filter = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:-1:-1,setsar=1,fps={fps},"
            f"zoompan=z='min(zoom+0.0005,1.5)':d={zoompan_duration}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}[bg];"
        )

        filter_complex = (
            f"{zoompan_filter}"
            f"[bg]{','.join(drawtext_filters)}[outv]"
        )

        # Komuta filtreleri ve output ayarlarını ekle
        command.extend([
            '-filter_complex', filter_complex,
            '-map', '[outv]',  # Filtrelenmiş videoyu çıkışa ekle
            '-map', '1:a',  # Ses dosyasını çıkışa ekle
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Orta hız/kalite dengesi
            '-c:a', 'aac',  # Ses codec
            '-shortest',  # Çıkışı en kısa medya dosyasına göre kes
            '-y',  # Üzerine yazma
            output_path
        ])

        return command
