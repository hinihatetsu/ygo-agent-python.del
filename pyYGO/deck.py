from typing import List

from pathlib import Path


class Deck:
    decks_dir: Path = Path.cwd() / 'Decks'
    def __init__(self, deck_name: str) -> None:
        self.name: str = deck_name
        self.main: List[int] = []
        self.extra: List[int] = []
        self.side: List[int] = []

        self.load()

    
    def load(self) -> None:
        deck: Path = self.decks_dir / self.name / (self.name + '.ydk')
        if not deck.exists():
            self.create()
        
        box: List[int] = self.main
        with deck.open() as f:
            for line in f.readlines():
                line = line.strip()
                if line == '#extra':
                    box = self.extra
                elif line == '!side':
                    box = self.side

                try:
                    id = int(line)
                    box.append(id)
                except ValueError as err:
                    pass


    def create(self) -> None:
        deck: Path = self.decks_dir / (self.name + '.ydk')
        if not deck.exists():
            raise ValueError(f'not found deck named "{self.name}"')

        deck_dir: Path = self.decks_dir / self.name
        if not deck_dir.exists():
            deck_dir.mkdir()

        deck.rename(deck_dir / deck.name)
        self.load()
        

    @property
    def count_main(self) -> int:
        return len(self.main)
    
    @property
    def count_extra(self) -> int:
        return len(self.extra)

    @property
    def count_side(self) -> int:
        return len(self.side)

    @property
    def count(self) -> int:
        return self.count_main + self.count_extra + self.count_side
                
