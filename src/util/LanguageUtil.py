import csv

from dotenv import load_dotenv


class LanguageInfo:
    def __init__(self, language, voice_id):
        self.language: str = language
        self.voice_id: str = voice_id

load_dotenv()

languages_path = 'resource/languages.csv'

class LanguageUtil:
    def __init__(self):
        self.languages = self.get_languages()

    def get_languages(self):
        with open(languages_path, mode='r') as file:
            csvFile = csv.reader(file)
            languages = []
            for lines in csvFile:
                languages.append(LanguageInfo(lines[0], lines[1]))
            return languages

    def get_voice_id(self, language):
        for lang in self.languages:
            if lang.language == language:
                return lang.voice_id
        return None