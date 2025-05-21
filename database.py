import sqlite3
from contextlib import contextmanager
from typing import Tuple

PREDEFINED_CHARACTERS = [
    "Vivienne VanDerBloom",
    "Casey Penwright",
    "Bianca Cross",
    "Sebastian Blackwell",
    "Harper Quinn",
    "Dante Steele",
    "Nico Valentine",
    "Mimi Butterfield"
]

PREDEFINED_CHARACTER_CLUE_SETS = {
    # Character 1: Vivienne VanDerBloom
    1: [
        # Set 1
        [
            ["A", "Vivienne VanDerBloom - Clue A - Act 1 - Set 1"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 1 - Set 1"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 1 - Set 1"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 2 - Set 1"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 2 - Set 1"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 2 - Set 1"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 3 - Set 1"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 3 - Set 1"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Vivienne VanDerBloom - Clue A - Act 1 - Set 2"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 1 - Set 2"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 1 - Set 2"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 2 - Set 2"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 2 - Set 2"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 2 - Set 2"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 3 - Set 2"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 3 - Set 2"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Vivienne VanDerBloom - Clue A - Act 1 - Set 3"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 1 - Set 3"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 1 - Set 3"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 2 - Set 3"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 2 - Set 3"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 2 - Set 3"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 3 - Set 3"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 3 - Set 3"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 3 - Set 3"]
        ],
    ],

    # Character 2: Casey Penwright
    2: [
        # Set 1
        [
            ["A", "Casey Penwright - Clue A - Act 1 - Set 1"],
            ["B", "Casey Penwright - Clue B - Act 1 - Set 1"],
            ["C", "Casey Penwright - Clue C - Act 1 - Set 1"],
            ["A", "Casey Penwright - Clue A - Act 2 - Set 1"],
            ["B", "Casey Penwright - Clue B - Act 2 - Set 1"],
            ["C", "Casey Penwright - Clue C - Act 2 - Set 1"],
            ["A", "Casey Penwright - Clue A - Act 3 - Set 1"],
            ["B", "Casey Penwright - Clue B - Act 3 - Set 1"],
            ["C", "Casey Penwright - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Casey Penwright - Clue A - Act 1 - Set 2"],
            ["B", "Casey Penwright - Clue B - Act 1 - Set 2"],
            ["C", "Casey Penwright - Clue C - Act 1 - Set 2"],
            ["A", "Casey Penwright - Clue A - Act 2 - Set 2"],
            ["B", "Casey Penwright - Clue B - Act 2 - Set 2"],
            ["C", "Casey Penwright - Clue C - Act 2 - Set 2"],
            ["A", "Casey Penwright - Clue A - Act 3 - Set 2"],
            ["B", "Casey Penwright - Clue B - Act 3 - Set 2"],
            ["C", "Casey Penwright - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Casey Penwright - Clue A - Act 1 - Set 3"],
            ["B", "Casey Penwright - Clue B - Act 1 - Set 3"],
            ["C", "Casey Penwright - Clue C - Act 1 - Set 3"],
            ["A", "Casey Penwright - Clue A - Act 2 - Set 3"],
            ["B", "Casey Penwright - Clue B - Act 2 - Set 3"],
            ["C", "Casey Penwright - Clue C - Act 2 - Set 3"],
            ["A", "Casey Penwright - Clue A - Act 3 - Set 3"],
            ["B", "Casey Penwright - Clue B - Act 3 - Set 3"],
            ["C", "Casey Penwright - Clue C - Act 3 - Set 3"]
        ]
    ],

    # Character 3: Bianca Cross
    3: [
        # Set 1
        [
            ["A", "Bianca Cross - Clue A - Act 1 - Set 1"],
            ["B", "Bianca Cross - Clue B - Act 1 - Set 1"],
            ["C", "Bianca Cross - Clue C - Act 1 - Set 1"],
            ["A", "Bianca Cross - Clue A - Act 2 - Set 1"],
            ["B", "Bianca Cross - Clue B - Act 2 - Set 1"],
            ["C", "Bianca Cross - Clue C - Act 2 - Set 1"],
            ["A", "Bianca Cross - Clue A - Act 3 - Set 1"],
            ["B", "Bianca Cross - Clue B - Act 3 - Set 1"],
            ["C", "Bianca Cross - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Bianca Cross - Clue A - Act 1 - Set 2"],
            ["B", "Bianca Cross - Clue B - Act 1 - Set 2"],
            ["C", "Bianca Cross - Clue C - Act 1 - Set 2"],
            ["A", "Bianca Cross - Clue A - Act 2 - Set 2"],
            ["B", "Bianca Cross - Clue B - Act 2 - Set 2"],
            ["C", "Bianca Cross - Clue C - Act 2 - Set 2"],
            ["A", "Bianca Cross - Clue A - Act 3 - Set 2"],
            ["B", "Bianca Cross - Clue B - Act 3 - Set 2"],
            ["C", "Bianca Cross - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Bianca Cross - Clue A - Act 1 - Set 3"],
            ["B", "Bianca Cross - Clue B - Act 1 - Set 3"],
            ["C", "Bianca Cross - Clue C - Act 1 - Set 3"],
            ["A", "Bianca Cross - Clue A - Act 2 - Set 3"],
            ["B", "Bianca Cross - Clue B - Act 2 - Set 3"],
            ["C", "Bianca Cross - Clue C - Act 2 - Set 3"],
            ["A", "Bianca Cross - Clue A - Act 3 - Set 3"],
            ["B", "Bianca Cross - Clue B - Act 3 - Set 3"],
            ["C", "Bianca Cross - Clue C - Act 3 - Set 3"]
        ]
    ],

    # Character 4: Sebastian Blackwell
    4: [
        # Set 1
        [
            ["A", "Sebastian Blackwell - Clue A - Act 1 - Set 1"],
            ["B", "Sebastian Blackwell - Clue B - Act 1 - Set 1"],
            ["C", "Sebastian Blackwell - Clue C - Act 1 - Set 1"],
            ["A", "Sebastian Blackwell - Clue A - Act 2 - Set 1"],
            ["B", "Sebastian Blackwell - Clue B - Act 2 - Set 1"],
            ["C", "Sebastian Blackwell - Clue C - Act 2 - Set 1"],
            ["A", "Sebastian Blackwell - Clue A - Act 3 - Set 1"],
            ["B", "Sebastian Blackwell - Clue B - Act 3 - Set 1"],
            ["C", "Sebastian Blackwell - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Sebastian Blackwell - Clue A - Act 1 - Set 2"],
            ["B", "Sebastian Blackwell - Clue B - Act 1 - Set 2"],
            ["C", "Sebastian Blackwell - Clue C - Act 1 - Set 2"],
            ["A", "Sebastian Blackwell - Clue A - Act 2 - Set 2"],
            ["B", "Sebastian Blackwell - Clue B - Act 2 - Set 2"],
            ["C", "Sebastian Blackwell - Clue C - Act 2 - Set 2"],
            ["A", "Sebastian Blackwell - Clue A - Act 3 - Set 2"],
            ["B", "Sebastian Blackwell - Clue B - Act 3 - Set 2"],
            ["C", "Sebastian Blackwell - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Sebastian Blackwell - Clue A - Act 1 - Set 3"],
            ["B", "Sebastian Blackwell - Clue B - Act 1 - Set 3"],
            ["C", "Sebastian Blackwell - Clue C - Act 1 - Set 3"],
            ["A", "Sebastian Blackwell - Clue A - Act 2 - Set 3"],
            ["B", "Sebastian Blackwell - Clue B - Act 2 - Set 3"],
            ["C", "Sebastian Blackwell - Clue C - Act 2 - Set 3"],
            ["A", "Sebastian Blackwell - Clue A - Act 3 - Set 3"],
            ["B", "Sebastian Blackwell - Clue B - Act 3 - Set 3"],
            ["C", "Sebastian Blackwell - Clue C - Act 3 - Set 3"]
        ]
    ],

        # Character 5: Harper Quinn
    
    # Character 5: Harper Quinn    
    5: [
        # Set 1
        [
            ["A", "Harper Quinn - Clue A - Act 1 - Set 1"],
            ["B", "Harper Quinn - Clue B - Act 1 - Set 1"],
            ["C", "Harper Quinn - Clue C - Act 1 - Set 1"],
            ["A", "Harper Quinn - Clue A - Act 2 - Set 1"],
            ["B", "Harper Quinn - Clue B - Act 2 - Set 1"],
            ["C", "Harper Quinn - Clue C - Act 2 - Set 1"],
            ["A", "Harper Quinn - Clue A - Act 3 - Set 1"],
            ["B", "Harper Quinn - Clue B - Act 3 - Set 1"],
            ["C", "Harper Quinn - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Harper Quinn - Clue A - Act 1 - Set 2"],
            ["B", "Harper Quinn - Clue B - Act 1 - Set 2"],
            ["C", "Harper Quinn - Clue C - Act 1 - Set 2"],
            ["A", "Harper Quinn - Clue A - Act 2 - Set 2"],
            ["B", "Harper Quinn - Clue B - Act 2 - Set 2"],
            ["C", "Harper Quinn - Clue C - Act 2 - Set 2"],
            ["A", "Harper Quinn - Clue A - Act 3 - Set 2"],
            ["B", "Harper Quinn - Clue B - Act 3 - Set 2"],
            ["C", "Harper Quinn - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Harper Quinn - Clue A - Act 1 - Set 3"],
            ["B", "Harper Quinn - Clue B - Act 1 - Set 3"],
            ["C", "Harper Quinn - Clue C - Act 1 - Set 3"],
            ["A", "Harper Quinn - Clue A - Act 2 - Set 3"],
            ["B", "Harper Quinn - Clue B - Act 2 - Set 3"],
            ["C", "Harper Quinn - Clue C - Act 2 - Set 3"],
            ["A", "Harper Quinn - Clue A - Act 3 - Set 3"],
            ["B", "Harper Quinn - Clue B - Act 3 - Set 3"],
            ["C", "Harper Quinn - Clue C - Act 3 - Set 3"]
        ]
    ],

    # Character 6: Dante Steele
    6: [
        # Set 1
        [
            ["A", "Dante Steele - Clue A - Act 1 - Set 1"],
            ["B", "Dante Steele - Clue B - Act 1 - Set 1"],
            ["C", "Dante Steele - Clue C - Act 1 - Set 1"],
            ["A", "Dante Steele - Clue A - Act 2 - Set 1"],
            ["B", "Dante Steele - Clue B - Act 2 - Set 1"],
            ["C", "Dante Steele - Clue C - Act 2 - Set 1"],
            ["A", "Dante Steele - Clue A - Act 3 - Set 1"],
            ["B", "Dante Steele - Clue B - Act 3 - Set 1"],
            ["C", "Dante Steele - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Dante Steele - Clue A - Act 1 - Set 2"],
            ["B", "Dante Steele - Clue B - Act 1 - Set 2"],
            ["C", "Dante Steele - Clue C - Act 1 - Set 2"],
            ["A", "Dante Steele - Clue A - Act 2 - Set 2"],
            ["B", "Dante Steele - Clue B - Act 2 - Set 2"],
            ["C", "Dante Steele - Clue C - Act 2 - Set 2"],
            ["A", "Dante Steele - Clue A - Act 3 - Set 2"],
            ["B", "Dante Steele - Clue B - Act 3 - Set 2"],
            ["C", "Dante Steele - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Dante Steele - Clue A - Act 1 - Set 3"],
            ["B", "Dante Steele - Clue B - Act 1 - Set 3"],
            ["C", "Dante Steele - Clue C - Act 1 - Set 3"],
            ["A", "Dante Steele - Clue A - Act 2 - Set 3"],
            ["B", "Dante Steele - Clue B - Act 2 - Set 3"],
            ["C", "Dante Steele - Clue C - Act 2 - Set 3"],
            ["A", "Dante Steele - Clue A - Act 3 - Set 3"],
            ["B", "Dante Steele - Clue B - Act 3 - Set 3"],
            ["C", "Dante Steele - Clue C - Act 3 - Set 3"]
        ]
    ],

        # Character 7: Nico Valentine

    # Character 7: Nico Valentine
    7: [
        # Set 1
        [
            ["A", "Nico Valentine - Clue A - Act 1 - Set 1"],
            ["B", "Nico Valentine - Clue B - Act 1 - Set 1"],
            ["C", "Nico Valentine - Clue C - Act 1 - Set 1"],
            ["A", "Nico Valentine - Clue A - Act 2 - Set 1"],
            ["B", "Nico Valentine - Clue B - Act 2 - Set 1"],
            ["C", "Nico Valentine - Clue C - Act 2 - Set 1"],
            ["A", "Nico Valentine - Clue A - Act 3 - Set 1"],
            ["B", "Nico Valentine - Clue B - Act 3 - Set 1"],
            ["C", "Nico Valentine - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Nico Valentine - Clue A - Act 1 - Set 2"],
            ["B", "Nico Valentine - Clue B - Act 1 - Set 2"],
            ["C", "Nico Valentine - Clue C - Act 1 - Set 2"],
            ["A", "Nico Valentine - Clue A - Act 2 - Set 2"],
            ["B", "Nico Valentine - Clue B - Act 2 - Set 2"],
            ["C", "Nico Valentine - Clue C - Act 2 - Set 2"],
            ["A", "Nico Valentine - Clue A - Act 3 - Set 2"],
            ["B", "Nico Valentine - Clue B - Act 3 - Set 2"],
            ["C", "Nico Valentine - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Nico Valentine - Clue A - Act 1 - Set 3"],
            ["B", "Nico Valentine - Clue B - Act 1 - Set 3"],
            ["C", "Nico Valentine - Clue C - Act 1 - Set 3"],
            ["A", "Nico Valentine - Clue A - Act 2 - Set 3"],
            ["B", "Nico Valentine - Clue B - Act 2 - Set 3"],
            ["C", "Nico Valentine - Clue C - Act 2 - Set 3"],
            ["A", "Nico Valentine - Clue A - Act 3 - Set 3"],
            ["B", "Nico Valentine - Clue B - Act 3 - Set 3"],
            ["C", "Nico Valentine - Clue C - Act 3 - Set 3"]
        ]
    ],

    # Character 8: Mimi Butterfield
    8: [
        # Set 1
        [
            ["A", "Mimi Butterfield - Clue A - Act 1 - Set 1"],
            ["B", "Mimi Butterfield - Clue B - Act 1 - Set 1"],
            ["C", "Mimi Butterfield - Clue C - Act 1 - Set 1"],
            ["A", "Mimi Butterfield - Clue A - Act 2 - Set 1"],
            ["B", "Mimi Butterfield - Clue B - Act 2 - Set 1"],
            ["C", "Mimi Butterfield - Clue C - Act 2 - Set 1"],
            ["A", "Mimi Butterfield - Clue A - Act 3 - Set 1"],
            ["B", "Mimi Butterfield - Clue B - Act 3 - Set 1"],
            ["C", "Mimi Butterfield - Clue C - Act 3 - Set 1"]
        ],
        # Set 2
        [
            ["A", "Mimi Butterfield - Clue A - Act 1 - Set 2"],
            ["B", "Mimi Butterfield - Clue B - Act 1 - Set 2"],
            ["C", "Mimi Butterfield - Clue C - Act 1 - Set 2"],
            ["A", "Mimi Butterfield - Clue A - Act 2 - Set 2"],
            ["B", "Mimi Butterfield - Clue B - Act 2 - Set 2"],
            ["C", "Mimi Butterfield - Clue C - Act 2 - Set 2"],
            ["A", "Mimi Butterfield - Clue A - Act 3 - Set 2"],
            ["B", "Mimi Butterfield - Clue B - Act 3 - Set 2"],
            ["C", "Mimi Butterfield - Clue C - Act 3 - Set 2"]
        ],
        # Set 3
        [
            ["A", "Mimi Butterfield - Clue A - Act 1 - Set 3"],
            ["B", "Mimi Butterfield - Clue B - Act 1 - Set 3"],
            ["C", "Mimi Butterfield - Clue C - Act 1 - Set 3"],
            ["A", "Mimi Butterfield - Clue A - Act 2 - Set 3"],
            ["B", "Mimi Butterfield - Clue B - Act 2 - Set 3"],
            ["C", "Mimi Butterfield - Clue C - Act 2 - Set 3"],
            ["A", "Mimi Butterfield - Clue A - Act 3 - Set 3"],
            ["B", "Mimi Butterfield - Clue B - Act 3 - Set 3"],
            ["C", "Mimi Butterfield - Clue C - Act 3 - Set 3"]
        ]
    ]

}

class ClueData:
    def __init__(self, db_path='clue_data.db'):
        self.db_path = db_path
        # Initialize connection first
        self.conn = sqlite3.connect(db_path, timeout=10)
        self.conn.row_factory = sqlite3.Row
        # Then initialize tables
        self._initialize_db()
        self._seed_characters()
        self._seed_clues()
    
    @contextmanager
    def cursor(self):
        """Simple context manager for database operations"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def _initialize_db(self):
        """Initialize database tables"""
        with self.cursor() as c:
            # Create players table
            c.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    password TEXT,
                    is_murderer BOOLEAN DEFAULT 0,
                    is_accomplice BOOLEAN DEFAULT 0,
                    is_detective BOOLEAN DEFAULT 0,
                    is_investigator BOOLEAN DEFAULT 0,
                    has_completed BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create other tables
            c.execute('''
                CREATE TABLE IF NOT EXISTS clues (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    set_number INTEGER NOT NULL,
                    act INTEGER NOT NULL,
                    clue_number INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    FOREIGN KEY(character_id) REFERENCES players(id),
                    UNIQUE(character_id, set_number, act, clue_number)
                )
            ''')
            
            # game_clues table
            c.execute('''
                CREATE TABLE IF NOT EXISTS game_clues (
                    act INTEGER PRIMARY KEY,
                    clue1 TEXT,
                    clue2 TEXT,
                    clue3 TEXT,
                    reliability1 INTEGER,
                    reliability2 INTEGER,
                    reliability3 INTEGER
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS murder_clues (
                    murderer_id INTEGER,
                    act INTEGER,
                    clue_text TEXT,
                    is_reliable BOOLEAN,
                    PRIMARY KEY (murderer_id, act, clue_text)
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_act INTEGER DEFAULT 1,
                    game_status TEXT DEFAULT 'WAITING'
                )
            ''')
            
            # Initialize game state
            c.execute('INSERT OR IGNORE INTO game_state VALUES (1, 1, "WAITING")')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS investigator_hints (
                    act INTEGER,
                    character_id INTEGER,
                    character_name TEXT,
                    is_innocent BOOLEAN,
                    PRIMARY KEY (act, character_id)
                )
            ''')
            

    # ... keep all your other existing methods exactly as they were ...
    def commit(self):
        """Commit changes to the database"""
        conn = sqlite3.connect(self.db_path)
        conn.commit()
        conn.close()

    def save_game_state(self, current_act: int, game_status: str):
        with self.cursor() as c:
            c.execute('''
                UPDATE game_state
                SET current_act = ?, game_status = ?
                WHERE id = 1
            ''', (current_act, game_status))
        self.commit()

    def load_game_state(self) -> Tuple[int, str]:
        with self.cursor() as c:
            try:
                # First check if table exists
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_state'")
                if not c.fetchone():
                    # Create table if it doesn't exist
                    c.execute('''
                        CREATE TABLE game_state (
                            id INTEGER PRIMARY KEY CHECK (id = 1),
                            current_act INTEGER DEFAULT 1,
                            game_status TEXT DEFAULT 'WAITING'
                        )
                    ''')
                    # Insert default row
                    c.execute('INSERT INTO game_state VALUES (1, 1, "WAITING")')
                    return (1, "WAITING")
                
                # Now try to get the state
                c.execute('SELECT current_act, game_status FROM game_state WHERE id = 1')
                row = c.fetchone()
                
                if row:
                    return (row['current_act'], row['game_status'])
                else:
                    # Insert default row if table exists but is empty
                    c.execute('INSERT INTO game_state VALUES (1, 1, "WAITING")')
                    return (1, "WAITING")
                    
            except sqlite3.Error as e:
                print(f"Error loading game state: {e}")
                # Create fresh state if anything goes wrong
                c.execute('DROP TABLE IF EXISTS game_state')
                c.execute('''
                    CREATE TABLE game_state (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        current_act INTEGER DEFAULT 1,
                        game_status TEXT DEFAULT 'WAITING'
                    )
                ''')
                c.execute('INSERT INTO game_state VALUES (1, 1, "WAITING")')
                return (1, "WAITING")
    
    def _seed_characters(self):
        """Initialize the 8 core characters"""
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players')
            if c.fetchone()[0] == 0:
                for character in PREDEFINED_CHARACTERS:
                    c.execute('INSERT INTO players (name) VALUES (?)', (character,))

    def _seed_clues(self):
        """Seed all clues for all characters"""
        with self.cursor() as c:
            # Check if clues already exist
            c.execute('SELECT COUNT(*) FROM clues')
            if c.fetchone()[0] > 0:
                return
            
            # Verify we have all 8 characters
            c.execute('SELECT COUNT(*) FROM players')
            if c.fetchone()[0] != 8:
                raise ValueError("Database doesn't have all 8 characters")
            
            # Process all characters
            for character_id in range(1, 9):  # Characters 1-8
                if character_id not in PREDEFINED_CHARACTER_CLUE_SETS:
                    raise ValueError(f"Missing clue sets for character {character_id}")
                    
                clue_sets = PREDEFINED_CHARACTER_CLUE_SETS[character_id]
                
                # Process all 3 sets for this character
                for set_number in range(1, 4):  # Sets 1-3
                    if len(clue_sets) < set_number:
                        raise ValueError(f"Missing set {set_number} for character {character_id}")
                    
                    clue_set = clue_sets[set_number - 1]  # Get the specific set
                    
                    # Process all 9 clues in this set (3 acts × 3 clues)
                    for clue_idx, (_, description) in enumerate(clue_set):
                        act = (clue_idx // 3) + 1  # Acts 1-3
                        clue_number = (clue_idx % 3) + 1  # Clues 1-3
                        
                        try:
                            c.execute('''
                                INSERT INTO clues 
                                (character_id, set_number, act, clue_number, description)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (character_id, set_number, act, clue_number, description))
                        except sqlite3.IntegrityError as e:
                            print(f"Failed to insert clue for character {character_id}, set {set_number}, act {act}, clue {clue_number}")
                            raise e

            # Verify we inserted all clues
            c.execute('SELECT COUNT(*) FROM clues')
            count = c.fetchone()[0]
            if count != 216:
                raise ValueError(f"Expected 216 clues, only inserted {count}")
    
    def get_players_with_status(self):
        with self.cursor() as c:
            c.execute('SELECT id, name, has_completed FROM players ORDER BY id')
            return c.fetchall()
    
    def set_murderer_status(self, player_id, is_murderer):
        with self.cursor() as c:
            c.execute('UPDATE players SET is_murderer=? WHERE id=?', 
                     (is_murderer, player_id))
    
    def set_accomplice_status(self, player_id, is_accomplice):
        with self.cursor() as c:
            c.execute('UPDATE players SET is_accomplice=? WHERE id=?',
                     (is_accomplice, player_id))
    
    def mark_player_completed(self, player_id):
        with self.cursor() as c:
            c.execute('UPDATE players SET has_completed=1 WHERE id=?', (player_id,))

    # Clue methods
    def get_clues_for_character_set(self, character_id, set_number):
        """Get all clues for a specific character and set"""
        with self.cursor() as c:
            c.execute('''
                SELECT act, clue_number, description 
                FROM clues 
                WHERE character_id=? AND set_number=?
                ORDER BY act, clue_number
            ''', (character_id, set_number))
            return c.fetchall()
    
    def get_clues_for_character_set_act(self, character_id, set_number, act):
        """Get clues for specific character, set and act"""
        with self.cursor() as c:
            c.execute('''
                SELECT clue_number, description
                FROM clues
                WHERE character_id=? AND set_number=? AND act=?
                ORDER BY clue_number
            ''', (character_id, set_number, act))
            return c.fetchall()

    # Utility methods
    def check_murderer_count(self):
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_murderer=1')
            return c.fetchone()[0]
    
    def check_accomplice_count(self):
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_accomplice=1')
            return c.fetchone()[0]
    
    def get_character_name(self, character_id):
        with self.cursor() as c:
            c.execute('SELECT name FROM players WHERE id=?', (character_id,))
            result = c.fetchone()
            return result[0] if result else None