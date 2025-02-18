from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, llm
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


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

    @llm
    def llm_model(self):
        return ChatOpenAI(temperature=0.0,  # Set to 0 for deterministic output
                          model="gpt-4o",  # Using the GPT-4 Turbo model
                          max_tokens=8000)

    # @agent
    # def official_source_finder_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['official_source_finder_agent'],
    #         output_pydantic=AllInformation,
    #         verbose=True
    #     )

    @agent
    def script_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['script_writer_agent'],
            output_pydantic=AllInformation,
            verbose=True
        )

    @agent
    def script_reduction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['script_reduction_agent'],
            output_pydantic=AllInformation,
            verbose=True
        )

    # @task
    # def find_official_source_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['find_official_source_task'],
    #         output_pydantic=AllInformation,
    #     )

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
