#!/usr/bin/env python
import asyncio
import json
import os

from crewai.flow.flow import Flow, start, listen, or_
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from crews.everything_under_2_minutes_discovery_crew.everything_in_2_minutes_discovery_crew import Data, \
    EverythingIn2MinutesStoryCrew, Sentence
from crews.image_creator_crew.image_creator_crew import ImageCreatorCrew
from crews.text_and_speech_crew.text_and_speech_crew import TextToSpeechCrew
from crews.verse_discovery_crew.verse_discovery_crew import AllInformation, StoryWritingCrew, Verse
from crews.video_crew.video_crew import VideoGeneratorCrew
from src.util.VerseUtil import VerseUtil, VerseInfo
from util.LanguageUtil import LanguageUtil

load_dotenv()

os.environ["OTEL_SDK_DISABLED"] = "true"

DATE_FORMAT = "%Y%m%d_%H%M%S"
DOWNLOAD_FOLDER_NAME = "output/images"


class VerseFlowState(BaseModel):
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





class YesFlow(Flow[VerseFlowState]):
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

        texts = [self.state.all_information.surah_name_and_verse_numbers,
                 self.state.all_information.place_and_time_of_revelation,
                 self.state.all_information.tafsir_of_the_verses,
                 ] + [verse.text for verse in self.state.all_information.verses]

        inputs = {
            "input_text": "|".join(texts),
            "save_path": f"output/{self.state.all_information.language}/sound",
            "language": self.state.all_information.language,
            "voice_id": LanguageUtil().get_voice_id(self.state.all_information.language),
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
            "width": "1080",
            "height": "1920",
            "combined": "true"
        }
        VideoGeneratorCrew().crew().kickoff(inputs=inputs)




class EverythingIn2MinutesFlowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: Data = Data(
        language="Unknown",
        question="Unknown",
        tags="N/A",
        sentences=[]
    )
class EverythingIn2MinutesFlow(Flow[EverythingIn2MinutesFlowState]):
    # flow
    @start()
    def start_story(self):
        inputs = {
            'language': os.getenv("CURRENT_LANGUAGE"),
            'question': os.getenv("QUESTION")
        }

        result = EverythingIn2MinutesStoryCrew().crew().kickoff(inputs=inputs)
        self.state.data = Data(**result.pydantic.model_dump())

        #write response to a file in output folder, if output folder does not exist, create first
        output_dir = f"output/{self.state.data.language}"
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "response.json"), "w") as f:
            json.dump(result.pydantic.model_dump(), f)

    @listen("start_story")
    async def parallel_tasks(self):
        await asyncio.gather(
            self.text_to_speech(),
            self.create_image()
        )

    async def text_to_speech(self):
        texts = [sentence.text for sentence in self.state.data.sentences]
        inputs = {
            "input_text": "|".join(texts),
            "save_path": f"output/{self.state.data.language}/sound",
            "language": self.state.data.language,
            "voice_id": os.getenv("CALLUM_VOICE_ID"),
            "combined": "false"
        }
        await asyncio.to_thread(TextToSpeechCrew().crew().kickoff, inputs=inputs)

    async def create_image(self):
        inputs = {
            "prompt_list": self.state.data.sentences,
            "save_path": f"output/{self.state.data.language}/image",
            "number_of_images": len(self.state.data.sentences),
            "width": "1920",
            "height": "1080"
        }
        await asyncio.to_thread(ImageCreatorCrew().crew().kickoff, inputs=inputs)

    @listen("parallel_tasks")
    def generate_video(self):
        language = os.getenv("CURRENT_LANGUAGE")
        inputs = {
            "audio_files_folder_path": f"output/{language}/sound",
            "timeline_files_folder_path": f"output/{language}/text",
            "source_folder":  f"output/{language}/image",
            "save_path": f"output/{language}/video",
            "width": "1920",
            "height": "1080",
            "combined": "true"
        }
        VideoGeneratorCrew().crew().kickoff(inputs=inputs)


class VideoGenerationFlow(Flow):
    @start()
    def create_video(self):
        YesFlow().generate_video()


def kickoff():
    if os.getenv("PROJECT") == "quran":
        yes_flow = YesFlow()
        yes_flow.kickoff()
    else:
        everything_in_2_minutes_flow = EverythingIn2MinutesFlow()
        everything_in_2_minutes_flow.kickoff()


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
