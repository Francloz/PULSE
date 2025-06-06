#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from crew import MapperCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'query': 'Count how many Hispanic male patients over the age of 50 were diagnosed with type 2 diabetes and underwent a coronary artery bypass graft procedure in the last five years?',
    }

    try:
        result = MapperCrew().crew().kickoff(inputs=inputs)
        print(result)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'query': 'Count how many Hispanic male patients over the age of 50 were diagnosed with type 2 diabetes and underwent a coronary artery bypass graft procedure in the last five years?',
    }

    try:
        MapperCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        MapperCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'query': 'Count how many Hispanic male patients over the age of 50 were diagnosed with type 2 diabetes and underwent a coronary artery bypass graft procedure in the last five years?',
    }
    
    try:
        MapperCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()