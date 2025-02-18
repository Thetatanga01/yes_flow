#!/usr/bin/env python
import os

from crewai.flow.flow import Flow, start, listen
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from crews.text_and_speech_crew.text_and_speech_crew import TextToSpeechCrew
from crews.verse_discovery_crew.verse_discovery_crew import AllInformation, StoryWritingCrew, Verse
from crews.video_crew.video_crew import VideoGeneratorCrew
from src.util.VerseUtil import VerseUtil, VerseInfo

load_dotenv()

os.environ["OTEL_SDK_DISABLED"] = "true"

DATE_FORMAT = "%Y%m%d_%H%M%S"
DOWNLOAD_FOLDER_NAME = "output/images"


class FlowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    all_information: AllInformation = AllInformation(
        language="Unknown",
        besmele="Unknown",
        sadakallahulazim="Unknown",
        surah_name_and_verse_numbers="Unknown",
        tafsir_of_the_verses="N/A",
        tags="N/A",
        place_and_time_of_revelation="Unknown",
        surah_name="Unknown",
        surah_number=0,
        verses=[],
        last_verse_number=0
    )
    current_verse: VerseInfo = VerseUtil().get_next_verse()


class YesFlow(Flow[FlowState]):

    # flow
    @start()
    def start_story(self):
        inputs = {
            'language': self.state.current_verse.language,
            'surah_name': VerseUtil().get_surah_name(self.state.current_verse.surah_no),
            "verse_no": self.state.current_verse.verse_no,
            "ending_verse_no": os.getenv("ENDING_VERSE_NO"),
        }

        result = StoryWritingCrew().crew().kickoff(inputs=inputs)
        self.state.all_information = AllInformation(**result.pydantic.model_dump())

    @listen("start_story")
    def save_last_verse(self):
        self.state.current_verse.verse_no = self.state.all_information.last_verse_number
        VerseUtil().save_verse(self.state.current_verse)

    @listen("save_last_verse")
    def text_to_speech(self):
        # add besmele to the first verse
        self.state.all_information.verses.insert(0, Verse(number=0, text=self.state.all_information.besmele))

        # add sadakallahulazim as last verse
        self.state.all_information.verses.append(
            Verse(number=self.state.all_information.last_verse_number + 1,
                  text=self.state.all_information.sadakallahulazim))

        intro = self.state.all_information.place_and_time_of_revelation + "\n\n" + \
                self.state.all_information.tafsir_of_the_verses + "\n\n"

        texts = [
                    self.state.all_information.surah_name_and_verse_numbers,
                    intro] + [verse.text for verse in self.state.all_information.verses]

        inputs = {
            "input_text": "|".join(texts),
            "save_path": f"output/{self.state.all_information.language}/sound",
            "language": self.state.all_information.language,
            "combined": "false"
        }
        TextToSpeechCrew().crew().kickoff(inputs=inputs)

    @listen("text_to_speech")
    def generate_video(self):
        language = os.getenv("CURRENT_LANGUAGE")
        inputs = {
            "audio_files_folder_path": f"output/{language}/sound",
            "timeline_files_folder_path": f"output/{language}/text",
            "video_folder": "resource/video",
            "save_path": f"output/{language}/video",
            "combined": "true"
        }
        VideoGeneratorCrew().crew().kickoff(inputs=inputs)


class VideoGenerationFlow(Flow):
    @start()
    def create_video(self):
        YesFlow().generate_video()


def kickoff():
    yes_flow = YesFlow()
    yes_flow.kickoff()


def kickoff_only_video_generation():
    video_flow = VideoGenerationFlow()
    video_flow.kickoff()


def kickoff_only_text_to_speech():
    language = "tr"
    texts = "Bugün hava çok güzel!|Yarın hava nasıl olacak?|Hava durumu nasıl olacak?".split("|")
    inputs = {
        "input_text": "|".join(texts),
        "save_path": f"output/{language}/sound",
        "language": language,
        "combined": "false"
    }
    TextToSpeechCrew().crew().kickoff(inputs=inputs)


def plot():
    yes_flow = YesFlow()
    yes_flow.plot()


if __name__ == "__main__":
    if os.getenv("FLOW") == "video":
        kickoff_only_video_generation()
    if os.getenv("TEST") == "tts":
        kickoff_only_text_to_speech()
    else:
        kickoff()
    # plot()
