import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from tools.downloader_tool import DownloaderTool
from tools.image_generator_tool import ImageGeneratorTool

load_dotenv()


@CrewBase
class ImageCreatorCrew:
    """Image Creator Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    chatgpt_llm = LLM(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        max_tokens=8000,
        temperature=0.0
    )

    @agent
    def visual_artist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['visual_artist_agent'],
            tools=[ImageGeneratorTool()],
            verbose=True,
            llm=self.chatgpt_llm
        )

    @task
    def create_image_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_image_task']
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
