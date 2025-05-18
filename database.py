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
        # Set 4
        [
            ["A", "Vivienne VanDerBloom - Clue A - Act 1 - Set 4"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 1 - Set 4"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 1 - Set 4"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 2 - Set 4"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 2 - Set 4"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 2 - Set 4"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 3 - Set 4"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 3 - Set 4"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Vivienne VanDerBloom - Clue A - Act 1 - Set 5"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 1 - Set 5"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 1 - Set 5"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 2 - Set 5"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 2 - Set 5"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 2 - Set 5"],
            ["A", "Vivienne VanDerBloom - Clue A - Act 3 - Set 5"],
            ["B", "Vivienne VanDerBloom - Clue B - Act 3 - Set 5"],
            ["C", "Vivienne VanDerBloom - Clue C - Act 3 - Set 5"]
        ]
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
        ],
        # Set 4
        [
            ["A", "Casey Penwright - Clue A - Act 1 - Set 4"],
            ["B", "Casey Penwright - Clue B - Act 1 - Set 4"],
            ["C", "Casey Penwright - Clue C - Act 1 - Set 4"],
            ["A", "Casey Penwright - Clue A - Act 2 - Set 4"],
            ["B", "Casey Penwright - Clue B - Act 2 - Set 4"],
            ["C", "Casey Penwright - Clue C - Act 2 - Set 4"],
            ["A", "Casey Penwright - Clue A - Act 3 - Set 4"],
            ["B", "Casey Penwright - Clue B - Act 3 - Set 4"],
            ["C", "Casey Penwright - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Casey Penwright - Clue A - Act 1 - Set 5"],
            ["B", "Casey Penwright - Clue B - Act 1 - Set 5"],
            ["C", "Casey Penwright - Clue C - Act 1 - Set 5"],
            ["A", "Casey Penwright - Clue A - Act 2 - Set 5"],
            ["B", "Casey Penwright - Clue B - Act 2 - Set 5"],
            ["C", "Casey Penwright - Clue C - Act 2 - Set 5"],
            ["A", "Casey Penwright - Clue A - Act 3 - Set 5"],
            ["B", "Casey Penwright - Clue B - Act 3 - Set 5"],
            ["C", "Casey Penwright - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Bianca Cross - Clue A - Act 1 - Set 4"],
            ["B", "Bianca Cross - Clue B - Act 1 - Set 4"],
            ["C", "Bianca Cross - Clue C - Act 1 - Set 4"],
            ["A", "Bianca Cross - Clue A - Act 2 - Set 4"],
            ["B", "Bianca Cross - Clue B - Act 2 - Set 4"],
            ["C", "Bianca Cross - Clue C - Act 2 - Set 4"],
            ["A", "Bianca Cross - Clue A - Act 3 - Set 4"],
            ["B", "Bianca Cross - Clue B - Act 3 - Set 4"],
            ["C", "Bianca Cross - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Bianca Cross - Clue A - Act 1 - Set 5"],
            ["B", "Bianca Cross - Clue B - Act 1 - Set 5"],
            ["C", "Bianca Cross - Clue C - Act 1 - Set 5"],
            ["A", "Bianca Cross - Clue A - Act 2 - Set 5"],
            ["B", "Bianca Cross - Clue B - Act 2 - Set 5"],
            ["C", "Bianca Cross - Clue C - Act 2 - Set 5"],
            ["A", "Bianca Cross - Clue A - Act 3 - Set 5"],
            ["B", "Bianca Cross - Clue B - Act 3 - Set 5"],
            ["C", "Bianca Cross - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Sebastian Blackwell - Clue A - Act 1 - Set 4"],
            ["B", "Sebastian Blackwell - Clue B - Act 1 - Set 4"],
            ["C", "Sebastian Blackwell - Clue C - Act 1 - Set 4"],
            ["A", "Sebastian Blackwell - Clue A - Act 2 - Set 4"],
            ["B", "Sebastian Blackwell - Clue B - Act 2 - Set 4"],
            ["C", "Sebastian Blackwell - Clue C - Act 2 - Set 4"],
            ["A", "Sebastian Blackwell - Clue A - Act 3 - Set 4"],
            ["B", "Sebastian Blackwell - Clue B - Act 3 - Set 4"],
            ["C", "Sebastian Blackwell - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Sebastian Blackwell - Clue A - Act 1 - Set 5"],
            ["B", "Sebastian Blackwell - Clue B - Act 1 - Set 5"],
            ["C", "Sebastian Blackwell - Clue C - Act 1 - Set 5"],
            ["A", "Sebastian Blackwell - Clue A - Act 2 - Set 5"],
            ["B", "Sebastian Blackwell - Clue B - Act 2 - Set 5"],
            ["C", "Sebastian Blackwell - Clue C - Act 2 - Set 5"],
            ["A", "Sebastian Blackwell - Clue A - Act 3 - Set 5"],
            ["B", "Sebastian Blackwell - Clue B - Act 3 - Set 5"],
            ["C", "Sebastian Blackwell - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Harper Quinn - Clue A - Act 1 - Set 4"],
            ["B", "Harper Quinn - Clue B - Act 1 - Set 4"],
            ["C", "Harper Quinn - Clue C - Act 1 - Set 4"],
            ["A", "Harper Quinn - Clue A - Act 2 - Set 4"],
            ["B", "Harper Quinn - Clue B - Act 2 - Set 4"],
            ["C", "Harper Quinn - Clue C - Act 2 - Set 4"],
            ["A", "Harper Quinn - Clue A - Act 3 - Set 4"],
            ["B", "Harper Quinn - Clue B - Act 3 - Set 4"],
            ["C", "Harper Quinn - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Harper Quinn - Clue A - Act 1 - Set 5"],
            ["B", "Harper Quinn - Clue B - Act 1 - Set 5"],
            ["C", "Harper Quinn - Clue C - Act 1 - Set 5"],
            ["A", "Harper Quinn - Clue A - Act 2 - Set 5"],
            ["B", "Harper Quinn - Clue B - Act 2 - Set 5"],
            ["C", "Harper Quinn - Clue C - Act 2 - Set 5"],
            ["A", "Harper Quinn - Clue A - Act 3 - Set 5"],
            ["B", "Harper Quinn - Clue B - Act 3 - Set 5"],
            ["C", "Harper Quinn - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Dante Steele - Clue A - Act 1 - Set 4"],
            ["B", "Dante Steele - Clue B - Act 1 - Set 4"],
            ["C", "Dante Steele - Clue C - Act 1 - Set 4"],
            ["A", "Dante Steele - Clue A - Act 2 - Set 4"],
            ["B", "Dante Steele - Clue B - Act 2 - Set 4"],
            ["C", "Dante Steele - Clue C - Act 2 - Set 4"],
            ["A", "Dante Steele - Clue A - Act 3 - Set 4"],
            ["B", "Dante Steele - Clue B - Act 3 - Set 4"],
            ["C", "Dante Steele - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Dante Steele - Clue A - Act 1 - Set 5"],
            ["B", "Dante Steele - Clue B - Act 1 - Set 5"],
            ["C", "Dante Steele - Clue C - Act 1 - Set 5"],
            ["A", "Dante Steele - Clue A - Act 2 - Set 5"],
            ["B", "Dante Steele - Clue B - Act 2 - Set 5"],
            ["C", "Dante Steele - Clue C - Act 2 - Set 5"],
            ["A", "Dante Steele - Clue A - Act 3 - Set 5"],
            ["B", "Dante Steele - Clue B - Act 3 - Set 5"],
            ["C", "Dante Steele - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Nico Valentine - Clue A - Act 1 - Set 4"],
            ["B", "Nico Valentine - Clue B - Act 1 - Set 4"],
            ["C", "Nico Valentine - Clue C - Act 1 - Set 4"],
            ["A", "Nico Valentine - Clue A - Act 2 - Set 4"],
            ["B", "Nico Valentine - Clue B - Act 2 - Set 4"],
            ["C", "Nico Valentine - Clue C - Act 2 - Set 4"],
            ["A", "Nico Valentine - Clue A - Act 3 - Set 4"],
            ["B", "Nico Valentine - Clue B - Act 3 - Set 4"],
            ["C", "Nico Valentine - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Nico Valentine - Clue A - Act 1 - Set 5"],
            ["B", "Nico Valentine - Clue B - Act 1 - Set 5"],
            ["C", "Nico Valentine - Clue C - Act 1 - Set 5"],
            ["A", "Nico Valentine - Clue A - Act 2 - Set 5"],
            ["B", "Nico Valentine - Clue B - Act 2 - Set 5"],
            ["C", "Nico Valentine - Clue C - Act 2 - Set 5"],
            ["A", "Nico Valentine - Clue A - Act 3 - Set 5"],
            ["B", "Nico Valentine - Clue B - Act 3 - Set 5"],
            ["C", "Nico Valentine - Clue C - Act 3 - Set 5"]
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
        ],
        # Set 4
        [
            ["A", "Mimi Butterfield - Clue A - Act 1 - Set 4"],
            ["B", "Mimi Butterfield - Clue B - Act 1 - Set 4"],
            ["C", "Mimi Butterfield - Clue C - Act 1 - Set 4"],
            ["A", "Mimi Butterfield - Clue A - Act 2 - Set 4"],
            ["B", "Mimi Butterfield - Clue B - Act 2 - Set 4"],
            ["C", "Mimi Butterfield - Clue C - Act 2 - Set 4"],
            ["A", "Mimi Butterfield - Clue A - Act 3 - Set 4"],
            ["B", "Mimi Butterfield - Clue B - Act 3 - Set 4"],
            ["C", "Mimi Butterfield - Clue C - Act 3 - Set 4"]
        ],
        # Set 5
        [
            ["A", "Mimi Butterfield - Clue A - Act 1 - Set 5"],
            ["B", "Mimi Butterfield - Clue B - Act 1 - Set 5"],
            ["C", "Mimi Butterfield - Clue C - Act 1 - Set 5"],
            ["A", "Mimi Butterfield - Clue A - Act 2 - Set 5"],
            ["B", "Mimi Butterfield - Clue B - Act 2 - Set 5"],
            ["C", "Mimi Butterfield - Clue C - Act 2 - Set 5"],
            ["A", "Mimi Butterfield - Clue A - Act 3 - Set 5"],
            ["B", "Mimi Butterfield - Clue B - Act 3 - Set 5"],
            ["C", "Mimi Butterfield - Clue C - Act 3 - Set 5"]
        ]
    ]

}


class ClueData:
    @contextmanager
    def cursor(self):
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
        
    def __init__(self, db_path='clue_data.db'):
        self.db_path = db_path
        self._initialize_db()
        self._seed_characters()
        self._seed_clues()
    
    def _initialize_db(self):
        with self.cursor() as c:
            # Players table
            c.execute('''CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        is_murderer BOOLEAN DEFAULT NULL,
                        is_accomplice BOOLEAN DEFAULT 0,
                        has_completed BOOLEAN DEFAULT 0
                        )''')
            
            # Character clue sets
            c.execute('''CREATE TABLE IF NOT EXISTS character_clue_sets (
                        set_id INTEGER PRIMARY KEY,
                        character_id INTEGER NOT NULL,
                        set_number INTEGER NOT NULL,
                        FOREIGN KEY(character_id) REFERENCES players(id),
                        UNIQUE(character_id, set_number)
                        )''')
            
            # Clues table
            c.execute('''CREATE TABLE IF NOT EXISTS clues (
                        id INTEGER PRIMARY KEY,
                        set_id INTEGER NOT NULL,
                        act INTEGER NOT NULL,
                        clue_label TEXT NOT NULL,
                        description TEXT NOT NULL,
                        FOREIGN KEY(set_id) REFERENCES character_clue_sets(set_id)
                        )''')
    
    def _seed_characters(self):
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players')
            if c.fetchone()[0] == 0:
                for character in PREDEFINED_CHARACTERS:
                    c.execute('INSERT INTO players (name) VALUES (?)', (character,))
    
    def _seed_clues(self):
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM character_clue_sets')
            if c.fetchone()[0] == 0:
                for char_id, sets in PREDEFINED_CHARACTER_CLUE_SETS.items():
                    for set_num, clues in enumerate(sets, 1):
                        # Create the clue set
                        c.execute('''INSERT INTO character_clue_sets 
                                    (character_id, set_number) 
                                    VALUES (?, ?)''', (char_id, set_num))
                        set_id = c.lastrowid
                        
                        # Insert all clues for this set
                        for act in range(1, 4):
                            for clue in clues[(act-1)*3 : act*3]:  # Get 3 clues per act
                                label, desc = clue
                                c.execute('''INSERT INTO clues 
                                        (set_id, act, clue_label, description)
                                        VALUES (?, ?, ?, ?)''',
                                        (set_id, act, label, desc))
    
    def get_character_clue_sets(self, character_id):
        """Get all clue sets for a specific character"""
        with self.cursor() as c:
            c.execute('''SELECT set_id, set_number 
                       FROM character_clue_sets 
                       WHERE character_id=?
                       ORDER BY set_number''', (character_id,))
            return c.fetchall()
    
    def get_clues_for_set(self, set_id):
        """Get all clues for a specific clue set"""
        with self.cursor() as c:
            c.execute('''SELECT act, clue_label, description, is_real, is_overlapping
                       FROM clues 
                       WHERE set_id=?
                       ORDER BY act, clue_label''', (set_id,))
            return c.fetchall()
    
    def check_accomplice_count(self):
        with self.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_accomplice=1')
            return c.fetchone()[0]
    
    # Player methods
    def get_players_with_status(self):
        with self.cursor() as c:
            c.execute('SELECT id, name, has_completed FROM players ORDER BY id')
            return c.fetchall()
    
    def set_murderer_status(self, player_id, is_murderer):
        with self.cursor() as c:
            c.execute('UPDATE players SET is_murderer=? WHERE id=?', 
                     (is_murderer, player_id))
    
    def mark_player_completed(self, player_id):
        with self.cursor() as c:
            c.execute('UPDATE players SET has_completed=1 WHERE id=?', (player_id,))
    
    # Clue methods
    def add_clue(self, act, clue_label, description, is_real, is_overlapping=False):
        with self.cursor() as c:
            c.execute('''INSERT INTO clues 
                      (act, clue_label, description, is_real, is_overlapping)
                      VALUES (?, ?, ?, ?, ?)''',
                      (act, clue_label, description, is_real, is_overlapping))
    
    def get_clues_by_act(self, act):
        with self.cursor() as c:
            c.execute('''SELECT clue_label, description, is_real, is_overlapping 
                       FROM clues WHERE act=? ORDER BY clue_label''', (act,))
            return c.fetchall()
    
    def get_acts(self):
        with self.cursor() as c:
            c.execute('SELECT DISTINCT act FROM clues ORDER BY act')
            return [row[0] for row in c.fetchall()]
        
    def get_character_clue_sets(self, character_id):
        # Get all clue sets for a specific character
        with self.cursor() as c:
            c.execute('''SELECT set_id, set_number 
                    FROM character_clue_sets 
                    WHERE character_id=?
                    ORDER BY set_number''', (character_id,))
            return c.fetchall()

    def get_clues_for_set_and_act(self, set_id, act):
        """Get clues for specific set and act"""
        with self.cursor() as c:
            c.execute('''SELECT clue_label, description 
                    FROM clues 
                    WHERE set_id=? AND act=?
                    ORDER BY clue_label''', (set_id, act))
            return c.fetchall()

    def get_character_name(self, character_id):
        """Get character name by ID"""
        with self.cursor() as c:
            c.execute('SELECT name FROM players WHERE id=?', (character_id,))
            result = c.fetchone()
            return result[0] if result else None