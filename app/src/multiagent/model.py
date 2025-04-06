from crewai import LLM

import config


def get_llm(model=config.MODEL_NAME, temperature=0.0, top_p=0):
    return LLM(
        model="ollama/" + model,
        base_url="http://localhost:11434",  # Ollama's API URL
        api_base="http://localhost:11434/api",  # Ensures it calls the right API
        litellm_provider="ollama",  # Explicitly set the provider to Ollama
        temperature=temperature,
        top_p=top_p,
        seed=0
    )


if __name__ == "__main__":
    import subprocess

    model = "gemma3:1b"
    # subprocess.run(["ollama", "pull", model], check=True)
    #
    # model_process = subprocess.Popen(["ollama", "run", model],
    #                                  stdout=subprocess.PIPE,
    #                                  stderr=subprocess.PIPE)

    from crewai import Agent, Task, Crew, Process, LLM
    from crewai.project import CrewBase, agent, task, crew
    import requests

    agents_config = {
        "pirate": {
            "role": "Pirate",
            "goal": "Answer the question 'What is the color of the sky?' in true pirate style.",
            "backstory": "You are a typical pirate who likes to talk in the mast of a ship and drink rum."
        }
    }
    # Task configuration to ask the question.
    tasks_config = {
        "sky_task": {
            "description": "What be the color of the sky?",
            "expected_output": "A description of the sky"  # Expected answer can be adjusted if needed.
        }
    }

    # Create an LLM instance pointing to your locally running model.
    local_llm = LLM(
        model="ollama/"+model,  # Model name (without :1b unless needed)
        base_url="http://localhost:11434",  # Ollama's API URL
        api_base="http://localhost:11434/api",  # Ensures it calls the right API
        litellm_provider="ollama"  # Explicitly set the provider to Ollama
    )

    @CrewBase
    class PirateCrew:
        @agent
        def pirate(self) -> Agent:
            return Agent(
                **agents_config["pirate"],
                verbose=True,
                llm=local_llm
            )

        @task
        def sky_task(self, myagent=None) -> Task:
            return Task(
                agent=myagent, **tasks_config["sky_task"],
            )

        @crew
        def crew(self) -> Crew:
            myagent = self.pirate()
            return Crew(
                agents=[myagent],
                tasks=[self.sky_task(myagent)],
                process=Process.sequential,
                verbose=True
            )

    """
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:1b",
            "prompt": "Why is the sky blue?",
            "stream": False
        }
    )
    print(response.json())
    """

    crew_instance = PirateCrew()
    result = crew_instance.crew().kickoff(inputs={})
    print("CrewAI Output:", result)

    # model_process.terminate()