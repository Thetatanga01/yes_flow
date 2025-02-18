from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, llm
from crewai_tools.tools.file_read_tool.file_read_tool import FileReadTool
from crewai_tools.tools.json_search_tool.json_search_tool import JSONSearchTool
from langchain_openai import ChatOpenAI

from tools.video_generator_tool import VideoGeneratorTool
from tools.youtube_upload_tool import YoutubeUploadTool


@CrewBase
class YoutubeUploadCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def llm_model(self):
        return ChatOpenAI(model="gpt-4o")

    @agent
    def video_uploader_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['video_uploader_agent'],
            tools=[YoutubeUploadTool()],
            verbose=True,
            max_iter=3
        )

    @task
    def upload_video_task(self) -> Task:
        return Task(
            config=self.tasks_config['upload_video_task'],
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
