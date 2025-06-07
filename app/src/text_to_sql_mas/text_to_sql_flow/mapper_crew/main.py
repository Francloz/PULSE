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
        # 'query': 'Count how many Hispanic male patients over the age of 50 were diagnosed with type 2 diabetes and underwent a coronary artery bypass graft procedure in the last five years?',
        'query': 'Identify pregnant women between ages 18-35 with gestational diabetes who delivered via cesarean section, had a birth weight measurement recorded for their newborn above the 90th percentile, received metformin therapy during pregnancy, and had at least two HbA1c lab results with values greater than 6.5% within 6 months prior to delivery, excluding patients with pre-existing type 1 or type 2 diabetes documented more than 12 months before conception.'
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