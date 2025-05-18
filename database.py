import sqlite3
from contextlib import contextmanager

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
        self._initialize_db()
        self._seed_characters()
    
    @contextmanager
    def cursor(self):
        """Database connection handler"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_db(self):
        """Create database tables with proper relationships"""
        with self.cursor() as c:
            # Players table - core characters
            c.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    is_murderer BOOLEAN DEFAULT NULL,
                    is_accomplice BOOLEAN DEFAULT 0,
                    has_completed BOOLEAN DEFAULT 0
                )
            ''')
            
            # Character clue sets - each character can have multiple sets
            c.execute('''
                CREATE TABLE IF NOT EXISTS character_clue_sets (
                    set_id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    set_number INTEGER NOT NULL,
                    FOREIGN KEY(character_id) REFERENCES players(id),
                    UNIQUE(character_id, set_number)
                )
            ''')
            
            # Clues table - actual clue content
            c.execute('''
                CREATE TABLE IF NOT EXISTS clues (
                    id INTEGER PRIMARY KEY,
                    set_id INTEGER NOT NULL,
                    act INTEGER NOT NULL,
                    clue_label TEXT NOT NULL,
                    description TEXT NOT NULL,
                    FOREIGN KEY(set_id) REFERENCES character_clue_sets(set_id)
                )
            ''')

    def _seed_characters(self):
        """Initialize the 8 core characters"""
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players')
            if c.fetchone()[0] == 0:
                for character in PREDEFINED_CHARACTERS:
                    c.execute('INSERT INTO players (name) VALUES (?)', (character,))

    # ===== PLAYER METHODS =====
    def get_players_with_status(self):
        """Get all players with completion status"""
        with self.cursor() as c:
            c.execute('SELECT id, name, has_completed FROM players ORDER BY id')
            return c.fetchall()
    
    def set_murderer_status(self, player_id, is_murderer):
        """Mark a player as murderer/not"""
        with self.cursor() as c:
            c.execute('UPDATE players SET is_murderer=? WHERE id=?', 
                     (is_murderer, player_id))
    
    def set_accomplice_status(self, player_id, is_accomplice):
        """Mark a player as accomplice/not"""
        with self.cursor() as c:
            c.execute('UPDATE players SET is_accomplice=? WHERE id=?',
                     (is_accomplice, player_id))
    
    def mark_player_completed(self, player_id):
        """Mark a player as having completed setup"""
        with self.cursor() as c:
            c.execute('UPDATE players SET has_completed=1 WHERE id=?', (player_id,))

    # ===== CLUE SET METHODS =====
    def create_clue_set(self, character_id, set_number):
        """Create a new clue set for a character"""
        with self.cursor() as c:
            c.execute('''
                INSERT INTO character_clue_sets (character_id, set_number)
                VALUES (?, ?)
            ''', (character_id, set_number))
            return c.lastrowid
    
    def get_character_clue_sets(self, character_id):
        """Get all clue sets for a character"""
        with self.cursor() as c:
            c.execute('''
                SELECT set_id, set_number 
                FROM character_clue_sets 
                WHERE character_id=?
                ORDER BY set_number
            ''', (character_id,))
            return c.fetchall()

    # ===== CLUE METHODS =====
    def add_clue_to_set(self, set_id, act, clue_label, description):
        """Add a clue to a specific set"""
        with self.cursor() as c:
            c.execute('''
                INSERT INTO clues (set_id, act, clue_label, description)
                VALUES (?, ?, ?, ?)
            ''', (set_id, act, clue_label, description))
    
    def get_clues_for_set_and_act(self, set_id, act):
        """Get all clues for a specific set and act"""
        with self.cursor() as c:
            c.execute('''
                SELECT clue_label, description 
                FROM clues 
                WHERE set_id=? AND act=?
                ORDER BY clue_label
            ''', (set_id, act))
            return c.fetchall()
    
    def get_all_clues_for_set(self, set_id):
        """Get all clues across all acts for a set"""
        with self.cursor() as c:
            c.execute('''
                SELECT act, clue_label, description
                FROM clues
                WHERE set_id=?
                ORDER BY act, clue_label
            ''', (set_id,))
            return c.fetchall()

    # ===== UTILITY METHODS =====
    def check_murderer_count(self):
        """Count how many murderers are marked"""
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_murderer=1')
            return c.fetchone()[0]
    
    def check_accomplice_count(self):
        """Count how many accomplices are marked"""
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_accomplice=1')
            return c.fetchone()[0]
    
    def get_character_name(self, character_id):
        """Get a character's name by ID"""
        with self.cursor() as c:
            c.execute('SELECT name FROM players WHERE id=?', (character_id,))
            result = c.fetchone()
            return result[0] if result else None