import csv
import os

from dotenv import load_dotenv


class VerseInfo:
    def __init__(self, language, surah_no, verse_no):
        self.language: str = language
        self.surah_no: int = surah_no
        self.verse_no: int = verse_no

load_dotenv()

surah_list_path = 'resource/Quran_Sure_Ayet_Listesi.csv'
save_path = 'resource/save.csv'
current_language = os.getenv('CURRENT_LANGUAGE')

class VerseUtil:
    def __init__(self):
        self.surah_verse_counts = self._load_surah_verse_counts()

    def _load_surah_verse_counts(self):
        surah_verse_counts = {}
        with open(surah_list_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for line_number, row in enumerate(reader, start=1):
                surah_verse_counts[line_number] = int(row['Ayet Sayısı'])
        return surah_verse_counts

    def get_next_verse(self):
        verse_info: VerseInfo = self.get_last_saved_verse()
        surah_no: int = int(verse_info.surah_no)
        verse_no: int = int(verse_info.verse_no)

        if surah_no in self.surah_verse_counts:
            if verse_no < self.surah_verse_counts[surah_no]:
                return VerseInfo(verse_info.language, surah_no, verse_no + 1)
            elif surah_no < len(self.surah_verse_counts):
                return VerseInfo(verse_info.language, surah_no + 1, 1)

        return VerseInfo(verse_info.language, 1, 1)

    def get_last_saved_verse(self):
        default = VerseInfo(current_language, 1, 1)  # Varsayılan olarak current_language kullan
        if not os.path.exists(save_path):
            return default

        with open(save_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["language"] == current_language:
                    return VerseInfo(row["language"], int(row["surah_no"]), int(row["verse_no"]))

        return default

    def save_verse(self, verse_info):
        # Eğer current_language tanımlı değilse işlem yapma
        if not current_language:
            print("current_language env değişkeni tanımlı değil!")
            return

        # Dosya varsa içeriği oku, yoksa boş bir liste başlat
        if os.path.exists(save_path):
            with open(save_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
        else:
            rows = []

        # Mevcut dili bul ve güncelle veya yeni satır ekle
        updated = False
        for row in rows:
            if row["language"] == current_language:
                row["surah_no"] = verse_info.surah_no
                row["verse_no"] = verse_info.verse_no
                updated = True
                break

        if not updated:
            rows.append({
                "language": current_language,
                "surah_no": verse_info.surah_no,
                "verse_no": verse_info.verse_no
            })

        # Güncellenmiş veriyi tekrar save.csv'ye yaz
        with open(save_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["language", "surah_no", "verse_no"])
            writer.writeheader()
            writer.writerows(rows)



    #gelen sure numarasınin Quran_Sure_Ayet_Listesi csv dosyasindaki hangi row a denk geldigine bakar ve oradaki sure adını döndürur
    def get_surah_name(self, surah_no):
        with open(surah_list_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for line_number, row in enumerate(reader, start=1):
                if line_number == surah_no:
                    return row['Sure']
        return "Unknown"
