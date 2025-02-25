#!/usr/bin/env python
import asyncio
import json
import os

from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel, ConfigDict

from crews.everything_under_2_minutes_discovery_crew.everything_in_2_minutes_discovery_crew import Data, \
    EverythingIn2MinutesStoryCrew
from crews.image_creator_crew.image_creator_crew import ImageCreatorCrew
from crews.speech_to_text_crew.speech_to_text_crew import SpeechToTextCrew
from crews.text_and_speech_crew.text_and_speech_crew import TextToSpeechCrew
from crews.video_crew.video_crew import VideoGeneratorCrew
from util.DimensionUtil import DimensionType, Provider
from util.VoiceUtil import VoiceType


class EverythingIn2MinutesFlowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: Data = Data(
        language="Unknown",
        question="Unknown",
        analogy="Unknown",
        tags="N/A",
        sentences=[]
    )


class EverythingIn2MinutesFlow(Flow[EverythingIn2MinutesFlowState]):
    # flow
    @start()
    def start_story(self):
        (width, height) = DimensionType.get_default().get(Provider.IMAGE)
        inputs = {
            'language': os.getenv("CURRENT_LANGUAGE"),
            'question': os.getenv("QUESTION"),
            'analogy': os.getenv("ANALOGY"),
            'dimension_type': f"{width}x{height}"
        }

        result = EverythingIn2MinutesStoryCrew().crew().kickoff(inputs=inputs)
        self.state.data = Data(**result.pydantic.model_dump())

        output_dir = f"output/{self.state.data.language}"
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "response.json"), "w") as f:
            json.dump(result.pydantic.model_dump(), f)

    async def text_to_speech(self):
        texts = [sentence.text for sentence in self.state.data.sentences]
        inputs = {
            "input_text": "|".join(texts),
            "save_path": f"output/{self.state.data.language}/sound",
            "language": self.state.data.language,
            "voice_id": VoiceType.get_default_value(),
            "combined": "false"
        }
        await asyncio.to_thread(TextToSpeechCrew().crew().kickoff, inputs=inputs)
        await asyncio.to_thread(self.speech_to_text)

    def speech_to_text(self):
        language = os.getenv("CURRENT_LANGUAGE")
        inputs = {
            "audio_files_folder_path": f"output/{language}/sound",
            "language_code": language,
            "save_path": f"output/{language}/text",
        }
        SpeechToTextCrew().crew().kickoff(inputs=inputs)

    async def create_image(self):
        inputs = {
            "prompt_list": self.state.data.sentences,
            "save_path": f"output/{self.state.data.language}/image",
            "number_of_images": len(self.state.data.sentences)
        }
        await asyncio.to_thread(ImageCreatorCrew().crew().kickoff, inputs=inputs)


    @listen("start_story")
    async def parallel_tasks(self):
        create_image_task = asyncio.create_task(self.create_image())
        await self.text_to_speech()
        await create_image_task

    @listen("parallel_tasks")
    def generate_video(self):
        language = os.getenv("CURRENT_LANGUAGE")
        inputs = {
            "audio_files_folder_path": f"output/{language}/sound",
            "timeline_files_folder_path": f"output/{language}/text",
            "source_folder": f"output/{language}/image",
            "save_path": f"output/{language}/video",
            "combined": "true"
        }
        VideoGeneratorCrew().crew().kickoff(inputs=inputs)
