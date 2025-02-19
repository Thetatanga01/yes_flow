import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, llm
from langchain_openai import ChatOpenAI

from tools.video_generator_tool import VideoGeneratorTool


@CrewBase
class VideoGeneratorCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # call gemini model
    gemini_llm = LLM(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini/gemini-2.0-flash",
        max_tokens=8000,
        temperature=0.1
    )

    chatgpt_llm = LLM(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        max_tokens=8000,
        temperature=0.1
    )

    @agent
    def video_creator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['video_creator_agent'],
            tools=[VideoGeneratorTool()],
            verbose=True,
            max_iter=3,
            llm=self.gemini_llm
        )

    @task
    def create_video_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_video_task'],
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
