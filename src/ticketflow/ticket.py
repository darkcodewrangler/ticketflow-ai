from typing import List


class Ticket:
    """Represents a support ticket"""
    
    def __init__(self, id: str, title: str, description: str, category: str, priority: str, status: str, created_at: str, updated_at: str, description_vector: List[float]):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.description_vector = description_vector