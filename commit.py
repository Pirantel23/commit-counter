from author import Author

class Commit:
    def __init__(self, author: Author, message: str) -> None:
        self.author = author
        self.message = message

    @classmethod
    def from_dict(self, data: dict) -> 'Commit':
        message = data['commit']['message']
        if message.startswith('Merge'):
            return None

        return self(
            author=Author.from_dict(data['commit']['author']),
            message=message
        )

    def __repr__(self) -> str:
        return f'Commit of {self.author}'
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Commit):
            return False
        return other.author.email == self.author.email
    
    def __hash__(self) -> int:
        return hash(self.author.email)