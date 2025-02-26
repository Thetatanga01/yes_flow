#!/usr/bin/env python
import os

from crewai.flow.flow import Flow, start
from dotenv import load_dotenv

from crews.text_and_speech_crew.text_and_speech_crew import TextToSpeechCrew
from flow.EverythingInSecondsFlow import EverythingIn2MinutesFlow
from flow.YesFlow import YesFlow

load_dotenv()

os.environ["OTEL_SDK_DISABLED"] = "true"


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
        everything_in_2_minutes_flow.generate_video()


#for test purposes
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
