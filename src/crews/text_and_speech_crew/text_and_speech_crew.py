from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, llm
from langchain_openai import ChatOpenAI

from tools.speech_to_text_tool import SpeechToTextTool
from tools.text_to_speech_tool import TextToSpeechTool


@CrewBase
class TextToSpeechCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def llm_model(self):
        return ChatOpenAI(model="gpt-4o")

    @agent
    def text_to_speech_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['text_to_speech_agent'],
            tools=[TextToSpeechTool()],
            verbose=True,
            max_iter=3
        )

    @agent
    def speech_to_text_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['speech_to_text_agent'],
            tools=[SpeechToTextTool()],
            verbose=True,
            max_iter=3
        )

    @task
    def convert_text_to_speech_task(self) -> Task:
        return Task(
            config=self.tasks_config['convert_text_to_speech_task'],
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
