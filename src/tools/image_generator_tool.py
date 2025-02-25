import os
import shutil
from typing import List

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from util.DimensionUtil import DimensionType, Provider

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = os.getenv("IMAGE_GENERATOR")


class Image(BaseModel):
    order_no: int = Field(..., description="The unique identifier of the video.")
    download_link: str = Field(..., description="The direct download link for the video.")


class ImageSearchResponse(BaseModel):
    images: List[Image] = Field(..., description="A list of images returned")


class ImageGeneratorToolInput(BaseModel):
    prompt_list: list = Field(..., description="Prompts for the image generation")
    save_path: str = Field(..., description="save path of the image")
    number_of_images: int = Field(..., description="Number of images to generate")


class ImageGeneratorTool(BaseTool):
    name: str = "Image Generator"
    description: str = "Generates images based on a given prompt."
    args_schema = ImageGeneratorToolInput

    def download(self, save_path: str, image: Image) -> dict:
        response = requests.get(image.download_link, stream=True)
        file_path = os.path.join(save_path, f"{image.order_no}.png")

        # Dosyayı kaydet
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)

    def _run(self, prompt_list: list, save_path: str, number_of_images) -> ImageSearchResponse:
        print(prompt_list)
        print(save_path)

        images: list[Image] = []

        shutil.rmtree(save_path, ignore_errors=True)
        os.makedirs(save_path, exist_ok=True)

        (width, height) = DimensionType.get_default().get(Provider.IMAGE)
        for i, prompt in enumerate(prompt_list):
            prompt = prompt.strip()
            try:
                full_prompt = prompt + ". Ultrarealistic and high resolution."
                print(f"{full_prompt} prompt'i ile resim oluşturuluyor...")
                response = client.images.generate(
                    model=model,
                    prompt=full_prompt,
                    size=f"{width}x{height}",
                    quality="standard",
                    n=1)
                image = Image(order_no=i, download_link=response.data[0].url)
                images.append(image)
                self.download(save_path=save_path, image=image)

            except Exception as e:
                print(f"Resim oluşturulurken hata: {e}")

        return ImageSearchResponse(images=images)
