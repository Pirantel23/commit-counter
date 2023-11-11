class Author:
    def __init__(self, name, email) -> None:
        self.name = name
        self.email = email
    
    @classmethod
    def from_dict(self, data: dict) -> 'Author':
        return self(
            name = data['name'],
            email = data['email']
        )
    
    def __repr__(self) -> str:
        return f'{self.name}({self.email})'