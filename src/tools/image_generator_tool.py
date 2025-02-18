import os
from typing import Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from openai import OpenAI
from openai.types import ImagesResponse
from pydantic import BaseModel, Field

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



#
# class ImageGeneratorTool(BaseTool):
#     name: str = "ImageGeneratorTool"
#     description: str = (
#         "creates images from dall e model"
#     )
#
#     def _run(self, argument: str) -> ImagesResponse:
#         return client.images.generate(
#             model="dall-e-3",
#             prompt="a white siamese cat",
#             size="1024x1024",
#             quality="standard",
#             n=1,
#         )



class ImageGeneratorTool(BaseTool):
    # name = "Image Generator"
    # description = "Generates images based on a given prompt."

    def _run(self, prompt: str):
        return client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1)

