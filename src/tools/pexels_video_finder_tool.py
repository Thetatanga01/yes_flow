import os
from typing import List

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field, BaseModel

load_dotenv()


class VideoFile(BaseModel):
    width: int = Field(..., description="The width of the video file.")
    height: int = Field(..., description="The height of the video file.")
    link: str = Field(..., description="The download link for the video file.")


class Video(BaseModel):
    id: str = Field(..., description="The unique identifier of the video.")
    url: str = Field(..., description="The URL of the video on Pexels.")
    preview_image: str = Field(..., description="The preview image of the video.")
    download_link: str = Field(..., description="The direct download link for the video.")


class VideoSearchResponse(BaseModel):
    videos: List[Video] = Field(..., description="A list of videos returned from the Pexels API.")


class PexelsVideoFinderToolInput(BaseModel):
    keyword: str = Field(..., description="The keyword to search for videos.")
    orientation: str = Field(..., description="The orientation of the video.")
    size: str = Field(..., description="The number of videos to retrieve.")


class PexelsVideoFinderTool(BaseTool):
    name: str = "pexels_video_finder"
    description: str = "Finds videos on Pexels based on a given keyword."
    args_schema = PexelsVideoFinderToolInput

    def _run(self, keyword: str, orientation: str, size: str) -> VideoSearchResponse:

        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        url = f"https://api.pexels.com/videos/search?query={keyword}&orientation={orientation}&per_page={size}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch videos: {response.status_code}")

        data = response.json()
        videos = []
        for video in data.get("videos", []):
            for file in video["video_files"]:
                #if (width is None or str(file["width"]) == width) and (height is None or str(file["height"]) == height):
                videos.append(Video(
                    id=keyword + "_" + str(video["id"]),
                    url=video["url"],
                    preview_image=video["image"],
                    download_link=file["link"]
                ))
                break

        return VideoSearchResponse(videos=videos)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async functionality is not implemented yet.")
