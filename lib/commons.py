from enum import Enum

class AutomatismType(Enum):
    Web = 'Web'
    Email = 'Email'
    
    def __str__(self):
        return self.name
