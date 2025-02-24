import os
from typing import List

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Verse(BaseModel):
    number: int
    text: str


class AllInformation(BaseModel):
    language: str
    besmele: str
    sadakallahulazim: str
    surah_name_and_verse_numbers: str
    tafsir_of_the_verses: str
    tags: str
    place_and_time_of_revelation: str
    surah_name: str
    surah_number: int
    verses: List[Verse]
    last_verse_number: int


@CrewBase
class StoryWritingCrew:
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
    def script_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['script_writer_agent'],
            output_pydantic=AllInformation,
            verbose=True,
            llm=self.chatgpt_llm
        )

    @agent
    def script_reduction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['script_reduction_agent'],
            output_pydantic=AllInformation,
            verbose=True,
            llm=self.chatgpt_llm
        )

    @task
    def script_writing(self) -> Task:
        return Task(
            config=self.tasks_config['script_writing'],
            output_pydantic=AllInformation,
        )

    @task
    def script_reduction(self) -> Task:
        return Task(
            config=self.tasks_config['script_reduction'],
            output_pydantic=AllInformation,
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
