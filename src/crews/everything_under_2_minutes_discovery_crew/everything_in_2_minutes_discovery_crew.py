import os
from typing import List

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools.tools.file_writer_tool.file_writer_tool import FileWriterTool
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Sentence(BaseModel):
    number: int
    image_prompt: str
    text: str


class Data(BaseModel):
    language: str
    analogy: str
    question: str
    tags: str
    sentences: List[Sentence]

@CrewBase
class EverythingIn2MinutesStoryCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    gemini_llm = LLM(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini/gemini-2.0-flash",
        max_tokens=8000,
        temperature=0.0
    )

    chatgpt_llm = LLM(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        max_tokens=8000,
        temperature=0.0
    )

    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'],
            output_pydantic=Data,
            verbose=True,
            llm=self.chatgpt_llm
        )

    # @agent
    # def editor_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['editor_agent'],
    #         output_pydantic=Data,
    #         verbose=True,
    #         llm=self.chatgpt_llm
    #     )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'],
            output_pydantic=Data,
        )

    # @task
    # def editing_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['editing_task'],
    #         output_pydantic=Data,
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
