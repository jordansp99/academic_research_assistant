from abc import ABC, abstractmethod

# this base agent uses a simple bdi architecture (beliefs, desires, intentions)
class BaseAgent(ABC):
    def __init__(self):
        self.beliefs = {}
        self.desires = {}
        self.intentions = []

    @abstractmethod
    def formulate_intentions(self, blackboard: dict):
        pass


    # the run method is the main entry point for an agent's execution cycle
    def run(self, blackboard: dict):
        self.formulate_intentions(blackboard)
        for intention in self.intentions:
            intention()
