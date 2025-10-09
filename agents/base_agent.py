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


    def run(self, blackboard: dict):
        self.formulate_intentions(blackboard)
        for intention in self.intentions:
            intention()
