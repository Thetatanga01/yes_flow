import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, llm
from langchain_openai import ChatOpenAI

from tools.speech_to_text_tool import SpeechToTextTool
from tools.text_to_speech_tool import TextToSpeechTool


@CrewBase
class SpeechToTextCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # call gemini model
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
    def speech_to_text_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['speech_to_text_agent'],
            tools=[SpeechToTextTool()],
            verbose=True,
            max_iter=3,
            llm=self.chatgpt_llm
        )

    @task
    def create_timeline_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_timeline_task'],
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
