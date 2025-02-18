from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, llm
from crewai_tools.tools.file_writer_tool.file_writer_tool import FileWriterTool
from langchain_openai import ChatOpenAI
from pydantic import Field, BaseModel

from tools.downloader_tool import DownloaderTool
#from tools.downloader_tool import DownloaderToolInput
from tools.pexels_video_finder_tool import PexelsVideoFinderTool, VideoSearchResponse


@CrewBase
class PexelsVideoFinderCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def llm_model(self):
        return ChatOpenAI(model="gpt-4o")

    @agent
    def pexels_video_finder_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['pexels_video_finder_agent'],
            tools=[PexelsVideoFinderTool()],
            verbose=True
        )

    @agent
    def pexels_video_downloader_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['pexels_video_downloader_agent'],
            tools=[DownloaderTool()],
            verbose=True
        )

    @task
    def pexels_find_video_task(self) -> Task:
        return Task(
            config=self.tasks_config['pexels_find_video_task'],
            output_pydantic=VideoSearchResponse
        )

    @task
    def video_download_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_download_task']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
