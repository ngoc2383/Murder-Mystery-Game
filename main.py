import os, random, getpass, sys, sqlite3, time
from database import ClueData
from typing import List, Tuple

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class ClueGameApp:
    def __init__(self):
        self.db = ClueData()
        self.host_password = "host123"
        self.murderer_passwords = {}
        self.accomplice_password = None
        self.accomplice_id = None
        self.detective_id = None  # Add these
        self.investigator_id = None
        
        # Initialize tables
        with self.db.cursor() as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS murder_clues (
                    murderer_id INTEGER,
                    act INTEGER,
                    clue_text TEXT,
                    is_reliable BOOLEAN,
                    PRIMARY KEY (murderer_id, act, clue_text)
                )
            ''')
        self.db.commit()

        try:
            self.current_act, self.game_state = self.db.load_game_state()
        except:
            self.current_act = 1
            self.game_state = "WAITING"
            self.db.save_game_state(self.current_act, self.game_state)
        
        # To verify state on startup
        self._verify_game_state()
    
    def _verify_game_state(self):
        """Ensure all tables and data are consistent"""
        with self.db.cursor() as c:
            # Create missing tables
            c.execute('''
                CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_act INTEGER DEFAULT 1,
                    game_status TEXT DEFAULT 'WAITING'
                )
            ''')
            
            # Initialize if empty
            c.execute('SELECT COUNT(*) FROM game_state')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO game_state VALUES (1, 1, "WAITING")')
            
            # Verify accomplice
            c.execute('SELECT id FROM players WHERE is_accomplice=1')
            accomplice = c.fetchone()
            if accomplice:
                self.accomplice_id = accomplice[0]
            
            # Verify murder clues
            c.execute('SELECT COUNT(*) FROM murder_clues')
            if c.fetchone()[0] == 0 and self.game_state == "IN PROCESS":
                print("Regenerating missing murder clues...")
                c.execute('SELECT id FROM players WHERE is_murderer=1')
                murderers = [row[0] for row in c.fetchall()]
                for m_id in murderers:
                    c.execute('SELECT id FROM players WHERE is_murderer=1 AND id!=?', (m_id,))
                    co_m = c.fetchone()[0]
                    self._generate_all_murder_clues(m_id, co_m)
            
            # Verify investigator
            c.execute('SELECT id FROM players WHERE is_investigator=1')
            investigator = c.fetchone()
            if investigator:
                self.investigator_id = investigator[0]
            
            # Verify detective
            c.execute('SELECT id FROM players WHERE is_detective=1')
            detective = c.fetchone()
            if detective:
                self.detective_id = detective[0]
        self.db.commit()
    
    def authenticate(self, prompt, password=None):
        clear_screen()
        print(f"=== {prompt.upper()} ===")
        attempt = getpass.getpass("Enter password: ")
        return attempt == password if password else attempt
    
    def check_murderer_count(self):
        with self.db.cursor() as c:
            c.execute('SELECT COUNT(*) FROM players WHERE is_murderer=1')
            return c.fetchone()[0]
    
    def reset_all_players(self):
        """Reset all player login statuses"""
        with self.db.cursor() as c:
            c.execute('''
                UPDATE players 
                SET is_murderer=NULL, is_accomplice=0, 
                    is_detective=0, is_investigator=0, 
                    has_completed=0
            ''')
        self.murderer_passwords = {}
        self.accomplice_id = None
        self.accomplice_password = None
        self.detective_id = None  # Add these new lines
        self.investigator_id = None
        self.db.commit()

    def reset_single_player(self, player_id: int):
        """Reset a single player's login status"""
        with self.db.cursor() as c:
            c.execute('''
                UPDATE players 
                SET is_murderer=NULL, is_accomplice=0,
                    is_detective=0, is_investigator=0,
                    has_completed=0
                WHERE id=?
            ''', (player_id,))
        
        # Clear any role references
        if player_id == self.accomplice_id:
            self.accomplice_id = None
            self.accomplice_password = None
        if player_id == self.detective_id:  # Add these new checks
            self.detective_id = None
        if player_id == self.investigator_id:
            self.investigator_id = None
            
        self.db.commit()
   
    def confirm_action(self, prompt):
        while True:
            response = input(f"{prompt} (yes/no): ").lower().strip()
            if response in ('yes', 'y'):
                return True
            elif response in ('no', 'n'):
                return False
            else:
                print("Please answer 'yes' or 'no'")

    def accomplice_login(self):
        """Handle accomplice login without revealing roles"""
        clear_screen()
        print("=== ACCOMPLICE LOGIN ===")
        
        # Show all characters regardless of role
        players = self.db.get_players_with_status()
        
        print("\nCharacters:")
        for idx, (player_id, name, _) in enumerate(players, 1):
            print(f"{idx}. {name}")
        
        try:
            choice = int(input("\nSelect your character: ")) - 1
            if 0 <= choice < len(players):
                player_id, name, _ = players[choice]
                
                # Verify this character is actually the accomplice
                with self.db.cursor() as c:
                    c.execute('SELECT is_accomplice FROM players WHERE id=?', (player_id,))
                    is_accomplice = c.fetchone()[0]
                
                '''
                if not is_accomplice:
                    print("This character is not the accomplice!")
                    input("Press Enter to continue...")
                    return
                '''
                password = getpass.getpass(f"{name}, enter your password: ")
                
                # Verify password
                with self.db.cursor() as c:
                    c.execute('SELECT password FROM players WHERE id=?', (player_id,))
                    result = c.fetchone()
                    if not result or result[0] != password:
                        print("Incorrect password or character!")
                        input("Press Enter to continue...")
                        return
                
                print(f"\nWelcome back, {name}!")
                self.accomplice_menu(name)
            else:
                print("Invalid selection!")
        except ValueError:
            print("Please enter a valid number")
        
        input("Press Enter to continue...")
    
    def setup_murderer(self, player_id, player_name):
        """Set up murderer with password"""
        # Set murderer status
        self.db.set_murderer_status(player_id, True)
        
        # Create password
        print(f"\n{player_name}, create your murderer password (min 4 chars):")
        while True:
            password = getpass.getpass("Password: ")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    # Store password in database
                    with self.db.cursor() as c:
                        c.execute('UPDATE players SET password=? WHERE id=?', 
                                (password, player_id))
                    self.db.mark_player_completed(player_id)
                    print(f"\nPassword set! Remember it, {player_name}!")
                    input("Press Enter to continue...")
                    break
            else:
                print("Password must be at least 4 characters")

    def setup_accomplice(self, player_id: int, player_name: str):
        """Set up an accomplice with a password"""
        with self.db.cursor() as c:
            # Clear any existing accomplice
            c.execute('UPDATE players SET is_accomplice=0, is_murderer=0 WHERE is_accomplice=1')
            
            # Set new accomplice
            c.execute('''
                UPDATE players 
                SET is_accomplice=1, is_murderer=0, has_completed=1 
                WHERE id=?
            ''', (player_id,))
            
        print("\nAs an accomplice, create a password:")
        while True:
            password = getpass.getpass("Password (min 4 chars): ")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    with self.db.cursor() as c:
                        c.execute('UPDATE players SET password=? WHERE id=?', (password, player_id))
                    self.accomplice_id = player_id
                    self.accomplice_password = password
                    break
            print("Password must be at least 4 characters")
        
        print(f"\n{player_name} registered as accomplice!")
        input("Press Enter to continue...")
    
    def murderer_login(self):
        """Handle murderer login without revealing roles"""
        clear_screen()
        print("=== MURDERER LOGIN ===")
        
        # Show all characters regardless of role
        players = self.db.get_players_with_status()
        
        print("\nCharacters:")
        for idx, (player_id, name, _) in enumerate(players, 1):
            print(f"{idx}. {name}")
        
        try:
            choice = int(input("\nSelect your character: ")) - 1
            if 0 <= choice < len(players):
                player_id, name, _ = players[choice]
                
                # Verify this character is actually a murderer
                with self.db.cursor() as c:
                    c.execute('SELECT is_murderer FROM players WHERE id=?', (player_id,))
                    is_murderer = c.fetchone()[0]
                
                '''
                if not is_murderer:
                    print("This character is not a murderer!")
                    input("Press Enter to continue...")
                    return
                '''

                password = getpass.getpass(f"{name}, enter your password: ")
                
                # Verify password
                with self.db.cursor() as c:
                    c.execute('SELECT password FROM players WHERE id=?', (player_id,))
                    result = c.fetchone()
                    if not result or result[0] != password:
                        print("Incorrect password or character!")
                        input("Press Enter to continue...")
                        return
                
                print(f"\nWelcome back, {name}!")
                self.murderer_menu(player_id, name)
            else:
                print("Invalid selection!")
        except ValueError:
            print("Please enter a valid number")
        
        input("Press Enter to continue...")
  
    def murderer_menu(self, player_id, name):
        """Updated menu for logged-in murderer"""
        while True:
            clear_screen()
            print(f"=== MURDERER MENU ({name}) ===")
            print("1. View Special Clues")
            print("2. View My Role Info")
            print("3. Logout")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self._view_murderer_special_clues(player_id)
            elif choice == '2':
                self._view_murderer_info(player_id, name)
            elif choice == '3':
                return
            else:
                print("Invalid choice")
                input("Press Enter to continue...")
  
    def view_murderers_accomplice(self):
        clear_screen()
        print("=== MURDERER IDENTITIES ===")
        
        with self.db.cursor() as c:
            c.execute('SELECT name FROM players WHERE is_murderer=1')
            murderers = c.fetchall()
        
        if not murderers:
            print("No murderers found yet!")
        else:
            print("The murderers are:")
            for i, (name,) in enumerate(murderers, 1):
                print(f"{i}. {name}")
        
        input("\nPress Enter to continue...")

    def view_accomplice_clues(self):
        clear_screen()
        print("=== SPECIAL CLUES ===")
        print("Select act to view accomplice clues:")
        print("1. Act 1")
        print("2. Act 2")
        print("3. Act 3")
        print("4. Back")
        
        while True:
            choice = input("Select act: ").strip()
            if choice in ('1', '2', '3'):
                act = int(choice)
                clues = self.db.get_accomplice_clues(act)
                
                clear_screen()
                print(f"=== ACT {act} ACCOMPLICE CLUES ===")
                for label, desc in clues:
                    print(f"\n{label}: {desc}")
                input("\nPress Enter to continue...")
                break
            elif choice == '4':
                break
            else:
                print("Invalid choice")

    def player_login(self):
        while True:
            clear_screen()
            print("=== PLAYER LOGIN ===")
            
            players = self.db.get_players_with_status()
            
            print("\nAvailable characters:")
            for idx, (player_id, name, completed) in enumerate(players, 1):
                status = " [COMPLETE]" if completed else ""
                print(f"{idx}. {name}{status}")
            
            if all(completed for _, _, completed in players):
                # Update game state to READY in both memory and database
                if self.game_state != "READY" and self.game_state != "IN PROCESS":
                    self.game_state = "READY"
                    self.db.save_game_state(self.current_act, self.game_state)
                
                # Always show verification option when all players are complete
                print("\nAll characters have completed login.")
                print("1. Verify roles")
                print("2. Back to main menu")
                
                choice = input("\nSelect option: ").strip()
                if choice == "1":
                    self.check_roles_setup()  # This will move to IN_PROGRESS if roles are valid
                    continue
                elif choice == "2":
                    return
                else:
                    print("Invalid choice")
                    input("Press Enter to continue...")
                    continue
                    
            try:
                choice = input("\nEnter character number (or 'back'): ").strip().lower()
                if choice == 'back' or choice == 'b':
                    return
                
                choice = int(choice)
                if 1 <= choice <= len(players):
                    selected_id, selected_name, completed = players[choice-1]
                    if completed:
                        print("This character has already completed login!")
                        input("Press Enter to continue...")
                        continue
                    
                    self.handle_role_selection(selected_id, selected_name)
                    
                    # Check if this was the last player to complete login
                    players = self.db.get_players_with_status()
                    if all(completed for _, _, completed in players):
                        self.game_state = "READY"
                        self.db.save_game_state(self.current_act, self.game_state)
                    
                    break
                
                print(f"Please enter 1-{len(players)} or 'back'")
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number or 'back'")
                input("Press Enter to continue...") 
   
    def check_roles_setup(self):
        clear_screen()
        print("=== ROLES VERIFICATION ===")
        
        try:
            # First get all role counts
            with self.db.cursor() as c:
                # Get all special roles
                c.execute('SELECT id FROM players WHERE is_accomplice=1')
                accomplice = c.fetchone()
                self.accomplice_id = accomplice[0] if accomplice else None
                
                c.execute('SELECT id FROM players WHERE is_detective=1')
                detective = c.fetchone()
                self.detective_id = detective[0] if detective else None
                
                c.execute('SELECT id FROM players WHERE is_investigator=1')
                investigator = c.fetchone()
                self.investigator_id = investigator[0] if investigator else None
                
                # Get counts
                murderer_count = self.check_murderer_count()
                accomplice_count = 1 if self.accomplice_id else 0
                detective_count = 1 if self.detective_id else 0
                investigator_count = 1 if self.investigator_id else 0
                
                # Check if all roles are properly assigned
                if (murderer_count == 2 and accomplice_count == 1 
                        and detective_count == 1 and investigator_count == 1):
                    print("\nAll roles properly assigned!")
                    print(f"- Murderers: {murderer_count}/2")
                    print(f"- Accomplice: {accomplice_count}/1")
                    print(f"- Detective: {detective_count}/1")
                    print(f"- Investigator: {investigator_count}/1")
                    
                    # Update game state immediately
                    self.game_state = "IN PROCESS"
                    self.db.save_game_state(self.current_act, self.game_state)
                    
                    # Generate game clues if needed
                    if not self._game_clues_exist():
                        self._assign_clue_sets()
                        self._select_final_clues_for_acts()
                    print("\nGame clues initialized!")
                    
                    # Get murderer IDs
                    c.execute('SELECT id FROM players WHERE is_murderer=1')
                    murderers = [row[0] for row in c.fetchall()]
            
            # Generate murder clues with separate cursor
            for murderer_id in murderers:
                with self.db.cursor() as c:
                    c.execute('SELECT id FROM players WHERE is_murderer=1 AND id!=?', (murderer_id,))
                    co_murderer_id = c.fetchone()[0]
                self._generate_all_murder_clues(murderer_id, co_murderer_id)
            print("Murderer intel generated!")
            
            # Generate investigator hints with separate cursor
            with self.db.cursor() as c:
                c.execute('SELECT COUNT(*) FROM investigator_hints')
                if c.fetchone()[0] == 0:
                    self._generate_investigator_hints()
            print("Investigator hints generated!")
            
        except Exception as e:
            print(f"\nERROR during role setup: {e}")
            import traceback
            traceback.print_exc()
        input("\nPress Enter to continue...")
   
    def handle_role_selection(self, player_id, player_name):
        while True:
            clear_screen()
            print(f"=== ROLE SELECTION ({player_name}) ===")
            print("1. Innocent")
            print("2. Murderer") 
            print("3. Accomplice")
            print("4. Detective")  # New option
            print("5. Investigator")  # New option
            
            choice = input("Select role: ").strip()
            
            if choice == "1":
                with self.db.cursor() as c:
                    c.execute('''
                        UPDATE players 
                        SET is_murderer=0, is_accomplice=0, is_detective=0, is_investigator=0, has_completed=1
                        WHERE id=?
                    ''', (player_id,))
                print(f"\n{player_name} registered as innocent.")
                input("Press Enter to continue...")
                break
                
            elif choice == "2":
                if self.accomplice_id == player_id:
                    print("\nCannot be both murderer and accomplice!")
                    input("Press Enter to continue...")
                    continue
                    
                if self.confirm_action(f"Confirm {player_name} is a murderer?"):
                    with self.db.cursor() as c:
                        c.execute('''
                            UPDATE players 
                            SET is_murderer=1, is_accomplice=0, is_detective=0, is_investigator=0, has_completed=1
                            WHERE id=?
                        ''', (player_id,))
                    self.setup_murderer(player_id, player_name)
                    break
                    
            elif choice == "3":
                with self.db.cursor() as c:
                    c.execute('SELECT is_murderer FROM players WHERE id=?', (player_id,))
                    if c.fetchone()[0] == 1:
                        print("\nCannot be both murderer and accomplice!")
                        input("Press Enter to continue...")
                        continue
                        
                if self.confirm_action(f"Confirm {player_name} is the accomplice?"):
                    self.setup_accomplice(player_id, player_name)
                    break
                    
            elif choice == "4":  # New: Detective
                if self.confirm_action(f"Confirm {player_name} is the detective?"):
                    self.setup_detective(player_id, player_name)
                    break
                    
            elif choice == "5":  # New: Investigator
                if self.confirm_action(f"Confirm {player_name} is an investigator?"):
                    self.setup_investigator(player_id, player_name)
                    break
                    
            else:
                print("Invalid choice")
                input("Press Enter to continue...")
  
    def _prepare_game_if_needed(self):
        """Prepare game if all players are registered but game isn't setup"""
        with self.db.cursor() as c:
            c.execute('SELECT COUNT(*) FROM game_clues')
            if c.fetchone()[0] == 0:  # Only prepare if no clues exist
                self._assign_clue_sets()
                self._select_final_clues_for_acts()
                print("\nGame setup complete! Clues have been assigned.")
                input("Press Enter to continue...")

    def initialize_game_clues(self):
        """Initialize game-wide clues using weighted selection when game is ready"""
        if not self._all_players_ready():
            return False
        
        # Assign clue sets to characters
        self._assign_clue_sets()
        
        # Select and store final clues for all acts
        self._select_final_clues_for_acts()
        return True

    def _all_players_ready(self) -> bool:
        """Check if all players have completed registration"""
        players = self.db.get_players_with_status()
        return all(completed for _, _, completed in players)

    def _assign_clue_sets(self):
        """Randomly assign clue sets to characters"""
        with self.db.cursor() as c:
            for char_id in range(1, 9):  # Assuming 8 players
                set_number = random.randint(1, 3)
                c.execute('UPDATE players SET has_completed=? WHERE id=?', 
                        (set_number, char_id))
        self.db.commit()

    def _select_final_clues_for_acts(self):
        """Select and store final clues for all acts with reliability ratings"""
        with self.db.cursor() as c:
            # Clear any existing game clues
            c.execute('DELETE FROM game_clues')
            
            for act in range(1, 4):  # Acts 1-3
                # Get the selected clues
                clues = self._select_weighted_clues(act)
                
                # Generate reliability ratings for these clues
                reliability_values = self._generate_reliability_ratings(clues)
                
                # Store clues with their reliability ratings
                c.execute('''
                    INSERT INTO game_clues 
                    (act, clue1, clue2, clue3, reliability1, reliability2, reliability3)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (act, clues[0], clues[1], clues[2], 
                    reliability_values[0], reliability_values[1], reliability_values[2]))
        self.db.commit()
 
    def _select_weighted_clues(self, act: int) -> List[str]:
        """Select 3 clues for an act with dynamic murderer weighting (randomized between 2-5)"""
        with self.db.cursor() as c:
            c.execute('''
                SELECT c.description, p.is_murderer
                FROM clues c
                JOIN players p ON c.character_id = p.id
                WHERE c.act = ? 
                AND c.set_number = p.has_completed
            ''', (act,))
            clue_rows = c.fetchall()

        if not clue_rows:
            return ["No clues available"] * 3

        # Assign dynamic weights based on murderer status
        clues = []
        weights = []
        for description, is_murderer in clue_rows:
            clues.append(description)
            if is_murderer:
                weights.append(random.randint(2, 5))  # Random weight for murderer clue
            else:
                weights.append(1)

        # Select 3 unique clues with weighted randomness
        selected = []
        remaining = list(zip(clues, weights))

        while len(selected) < 3 and remaining:
            remaining_clues, remaining_weights = zip(*remaining)
            chosen = random.choices(remaining_clues, weights=remaining_weights, k=1)[0]
            selected.append(chosen)
            remaining = [c for c in remaining if c[0] != chosen]

        return selected[:3]

    def get_game_clues(self, act: int) -> List[str]:
        """Get pre-formatted game clues for a specific act"""
        with self.db.cursor() as c:
            c.execute('SELECT clue1, clue2, clue3 FROM game_clues WHERE act=?', (act,))
            row = c.fetchone()
            if row:
                return [row['clue1'], row['clue2'], row['clue3']]
        return []
  
    def display_act_clues(self, act: int):
        """Display pre-formatted clues for a specific act"""
        clear_screen()
        print(f"=== ACT {act} CLUES ===")
        
        clues = self.get_game_clues(act)
        if not clues:
            print("\nERROR: No clues available!")
            print("Possible reasons:")
            print("- Not all players have completed registration")
            print("- Game setup hasn't run yet")
        else:
            print("\nClues revealed:")
            for i, clue in enumerate(clues, 1):
                print(f"{i}. {clue}")
        
        input("\nPress Enter to continue...")
    
    def advance_act(self):
        """Simply advance act since clues are pre-generated"""
        if self.current_act >= 3:
            self.game_state = "COMPLETED"
            print("\nGame completed! All acts finished.")
        else:
            self.current_act += 1
            print(f"\nAdvanced to Act {self.current_act}!")
        
        self.db.save_game_state(self.current_act, self.game_state)
        input("Press Enter to continue...") 
   
    def reset_options(self):
        """Reset game options while preserving player roles"""
        clear_screen()
        print("=== RESET OPTIONS ===")
        print("1. Reset All Clue Assignments")
        print("2. Reset Current Act")
        print("3. Reset All Player Checkin")
        print("4. Reset Single Player Checkin")
        print("5. Back to Host Menu")
        
        choice = input("Select an option: ").strip()
        
        if choice == '1':
            if self.confirm_action("Reset all clue set assignments and clues?"):
                with self.db.cursor() as c:
                    # Clear all clue tables
                    c.execute('DELETE FROM game_clues')
                    c.execute('DELETE FROM murder_clues')
                    c.execute('DELETE FROM investigator_hints')
                    
                    # Reset game state
                    self.current_act = 1
                    self.game_state = "READY"
                    c.execute('''
                        UPDATE game_state
                        SET current_act=1, game_status='READY'
                        WHERE id=1
                    ''')
                    
                    # Reassign clue sets randomly
                    for char_id in range(1, 9):  # Assuming 8 players
                        set_number = random.randint(1, 3)
                        c.execute('UPDATE players SET has_completed=? WHERE id=?', 
                                (set_number, char_id))
                    
                self.db.commit()
                print("\nAll clue assignments and clues have been reset!")
                print("Game state set to Act 1, READY")
                
        elif choice == '2':
            if self.confirm_action("Reset current act to Act 1?"):
                self.current_act = 1
                self.db.save_game_state(self.current_act, self.game_state)
                print("\nAct reset to Act 1!")
                
        elif choice == '3':
            if self.confirm_action("Reset all player checkins?"):
                self.reset_all_players()
                print("\nAll player checkins have been reset!")
                
        elif choice == '4':
            if self.confirm_action("Reset one player checkins?"):
                player_id = int(input("User ID to reset: "))
                self.reset_single_player(player_id)
                print("\nThis player checkins have been reset!")
                
        elif choice == '5':
            return
            
        else:
            print("Invalid choice")
        
        input("Press Enter to continue...")

    def _game_clues_exist(self) -> bool:
        """Check if game clues already exist"""
        with self.db.cursor() as c:
            c.execute('SELECT COUNT(*) FROM game_clues')
            return c.fetchone()[0] > 0 
  
    def view_murderers_host(self):
        clear_screen()
        print("=== MURDERER LIST ===")
        
        with self.db.cursor() as c:
            c.execute('SELECT name FROM players WHERE is_murderer=1')
            murderers = c.fetchall()
        
        if not murderers:
            print("No murderers selected yet!")
        else:
            print("Current murderers:")
            for i, (name,) in enumerate(murderers, 1):
                print(f"{i}. {name}")
        
        input("\nPress Enter to continue...")

    def view_accomplice(self):
        clear_screen()
        print("=== ACCOMPLICE INFO ===")
        
        if not self.accomplice_id:
            print("No accomplice selected yet!")
        else:
            with self.db.cursor() as c:
                c.execute('SELECT name FROM players WHERE id=?', (self.accomplice_id,))
                name = c.fetchone()[0]
                print(f"Accomplice: {name}")
        
        input("\nPress Enter to continue...")

    def host_clue_reveal(self):
        if not self.authenticate("HOST LOGIN", self.host_password):
            print("Invalid host password!")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print("=== HOST MENU ===\n")
            print(f"Game State: {self.game_state} | Current Act: {self.current_act}\n")
            print("1. Reveal Current Act Clues")
            print("2. View Murderers")
            print("3. View Accomplice")
            print("4. Reset Options")
            print("5. Advance Act")
            print("6. Restart Game (COMPLETE RESET)")
            print("7. Back to Main Menu")
            
            choice = input("\nSelect an option: ").strip()
            
            if choice == '1':
                if self.authenticate("HOST VERIFICATION", self.host_password):
                    self.display_act_clues(self.current_act)
            elif choice == '2':
                if self.authenticate("HOST VERIFICATION", self.host_password):
                    self.view_murderers_host()
            elif choice == '3':
                if self.authenticate("HOST VERIFICATION", self.host_password):
                    self.view_accomplice()
            elif choice == '4':
                self.reset_options()
            elif choice == '5':
                if self.authenticate("HOST VERIFICATION", self.host_password):
                    self.advance_act()
            elif choice == '6':
                self.restart_game()
            elif choice == '7':
                return
            else:
                print("Invalid choice. Please try again.")
                input("Press Enter to continue...")
   
    def restart_game(self):
        """Completely reset all game data and state including murder_clues and game_state"""
        if not self.authenticate("HOST VERIFICATION", self.host_password):
            print("Invalid host password!")
            input("Press Enter to continue...")
            return
        
        if not self.confirm_action("WARNING: This will ERASE ALL GAME DATA. Continue?"):
            print("Game reset cancelled.")
            input("Press Enter to continue...")
            return
        
        try:
            with self.db.cursor() as c:
                # Drop all game tables
                c.execute('DROP TABLE IF EXISTS players')
                c.execute('DROP TABLE IF EXISTS clues')
                c.execute('DROP TABLE IF EXISTS game_clues')
                c.execute('DROP TABLE IF EXISTS murder_clues')
                c.execute('DROP TABLE IF EXISTS investigator_hints')  # Drop the hints table
                c.execute('DROP TABLE IF EXISTS game_state')

                # Reinitialize database
                self.db._initialize_db()
                self.db._seed_characters()
                self.db._seed_clues()
                
                # Recreate special tables with proper structure
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
                
                # Add recreation of investigator_hints table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS investigator_hints (
                        act INTEGER,
                        character_id INTEGER,
                        character_name TEXT,
                        is_innocent BOOLEAN,
                        PRIMARY KEY (act, character_id)
                    )
                ''')
                
                # Initialize game_state with default values
                c.execute('''
                    INSERT INTO game_state (id, current_act, game_status)
                    VALUES (1, 1, 'WAITING')
                ''')
                
                # Reset all in-memory state
                self.murderer_passwords = {}
                self.accomplice_password = None
                self.accomplice_id = None
                self.current_act = 1
                self.game_state = "WAITING"

            self.db.commit()
            self.current_act, self.game_state = self.db.load_game_state()    
            print("\nGame completely reset! All data erased.")
            print("New game ready to be set up.")
            print(f"Current state: Act {self.current_act}, Status: {self.game_state}")
        except Exception as e:
            print(f"\nError resetting game: {str(e)}")
            # Emergency recovery - ensure critical tables exist
            with self.db.cursor() as c:
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
                # Add recreation of investigator_hints in emergency recovery
                c.execute('''
                    CREATE TABLE IF NOT EXISTS investigator_hints (
                        act INTEGER,
                        character_id INTEGER,
                        character_name TEXT,
                        is_innocent BOOLEAN,
                        PRIMARY KEY (act, character_id)
                    )
                ''')
                # Ensure at least one row exists in game_state
                c.execute('SELECT COUNT(*) FROM game_state')
                if c.fetchone()[0] == 0:
                    c.execute('INSERT INTO game_state VALUES (1, 1, "WAITING")')
            self.db.commit()
            print("Recovery complete - basic tables recreated")
        sys.exit()
  
    def accomplice_menu(self, name: str):
        """Special menu for the accomplice with weighted clues"""
        while True:
            clear_screen()
            print(f"=== ACCOMPLICE MENU ({name}) ===")
            print("1. View Special Clues")
            print("2. View My Role Info")
            print("3. Return to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_accomplice_clues_weighted()
            elif choice == '2':
                self.view_accomplice_info()
            elif choice == '3':
                return
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

    def _get_weighted_accomplice_clues(self, act: int) -> List[Tuple[str, int]]:
        """Get the same 3 game clues with probabilistic reliability ratings"""
        with self.db.cursor() as c:
            # Get the standard 3 game clues for this act
            c.execute('SELECT clue1, clue2, clue3, reliability1, reliability2, reliability3 FROM game_clues WHERE act=?', (act,))
            row = c.fetchone()
            
            if not row:
                return []
            
            clues = self._select_weighted_clues(act)
            # Check if we need to generate new reliability ratings
            if row['reliability1'] is None:
                return self._generate_reliability_ratings(clues)
                
            # Return existing weighted clues
            return [
                (row['clue1'], row['reliability1']),
                (row['clue2'], row['reliability2']),
                (row['clue3'], row['reliability3'])
            ]

    def _generate_reliability_ratings(self, clues: List[str]) -> List[int]:
        """Generate reliability ratings for clues (same for all special roles)"""
        reliability_values = []
        
        with self.db.cursor() as c:
            for clue in clues:
                try:
                    character_name = clue.split(' - ')[0].strip()
                except:
                    # Fallback if clue format is different
                    reliability_values.append(1)
                    continue
                    
                # Get character role info
                c.execute('''
                    SELECT is_murderer, is_accomplice 
                    FROM players 
                    WHERE name=?
                ''', (character_name,))
                result = c.fetchone()
                
                if not result:
                    reliability = 1
                else:
                    is_murderer = result['is_murderer']
                    is_accomplice = result['is_accomplice']
                    
                    # Unified reliability rating system
                    if is_murderer:
                        # Murderer's clue: 50% strong (3), 30% medium (2), 20% weak (1)
                        reliability = 3 if random.random() < 0.5 else (2 if random.random() < 0.6 else 1)
                    elif is_accomplice:
                        # Accomplice's clue: 40% medium (2), 35% strong (3), 25% weak (1)
                        reliability = 2 if random.random() < 0.4 else (3 if random.random() < 0.58 else 1)
                    else:
                        # Innocent's clue: 60% weak (1), 25% medium (2), 15% strong (3)
                        reliability = 1 if random.random() < 0.6 else (2 if random.random() < 0.71 else 3)
                
                reliability_values.append(reliability)
        
        return reliability_values
  
    def get_weighted_clues(self, act: int) -> List[Tuple[str, int]]:
        """Get clues with pre-generated reliability ratings"""
        with self.db.cursor() as c:
            c.execute('''
                SELECT clue1, clue2, clue3, reliability1, reliability2, reliability3 
                FROM game_clues 
                WHERE act=?
            ''', (act,))
            row = c.fetchone()
            
            if not row:
                return []
                
            return [
                (row['clue1'], row['reliability1']),
                (row['clue2'], row['reliability2']),
                (row['clue3'], row['reliability3'])
            ]

    def view_accomplice_clues_weighted(self):
        """Show standard 3 game clues with reliability ratings"""
        clear_screen()
        print(f"=== YOUR SPECIAL CLUES (ACT {self.current_act}) ===")
        
        clues = self.get_weighted_clues(self.current_act)
        
        if not clues:
            print("\nNo clues available for current act!")
            input("Press Enter to continue...")
            return
        
        print("\nThe same clues everyone sees, but you know which might be trustworthy:")
        for i, (clue, weight) in enumerate(clues, 1):
            print(f"\n{i}. {clue}")
            reliability_desc = {
                3: "★★★ Highly reliable",
                2: "★★☆ Moderately reliable",
                1: "★☆☆ Potentially unreliable"
            }.get(weight, "Unknown reliability")
            print(f"   {reliability_desc}")
        
        print("\nAccomplice Notes:")
        print("- ★★★ clues most likely point towards the murderer")
        print("- ★★☆ clues may point towards murderer")
        print("- ★☆☆ clues may be intentionally misleading")
        print("- Reliability ratings aren't perfect - trust your instincts!")
        input("\nPress Enter to continue...")

    def view_detective_clues_weighted(self):
        """Show standard 3 game clues with reliability ratings"""
        clear_screen()
        print(f"=== YOUR INVESTIGATION CLUES (ACT {self.current_act}) ===")
        
        clues = self.get_weighted_clues(self.current_act)
        
        if not clues:
            print("\nNo clues available for current act!")
            input("Press Enter to continue...")
            return
        
        print("\nThe same clues everyone sees, but you know which might be trustworthy:")
        for i, (clue, weight) in enumerate(clues, 1):
            print(f"\n{i}. {clue}")
            reliability_desc = {
                3: "★★★ Highly reliable",
                2: "★★☆ Moderately reliable",
                1: "★☆☆ Potentially unreliable"
            }.get(weight, "Unknown reliability")
            print(f"   {reliability_desc}")
        
        print("\nInvestigation Notes:")
        print("- ★★★ clues most likely point towards the murderer")
        print("- ★★☆ clues may point towards murderer")
        print("- ★☆☆ clues may be intentionally misleading")
        print("- Reliability ratings aren't perfect - trust your instincts!")
        
        input("\nPress Enter to continue...")
  
    def view_accomplice_info(self):
        """Show the accomplice's character information"""
        clear_screen()
        print(f"=== YOUR CHARACTER INFO ===")
        
        with self.db.cursor() as c:
            # Get character details
            c.execute('''
                SELECT name, password, is_accomplice
                FROM players 
                WHERE id=?
            ''', (self.accomplice_id,))
            result = c.fetchone()
            
        if result:
            print(f"\nCharacter Name: {result['name']}")
            print(f"Your Password: {result['password']}")
            print(f"Role: {'Accomplice' if result['is_accomplice'] else 'Unknown'}")
            print("\nRemember:")
            print("- You see reliability ratings on clues")
            print("- You don't know the murderers' identities")
            print("- Your clues may be more reliable than others")
        else:
            print("\nError: Character information not found!")
        
        input("\nPress Enter to continue...")

    def view_character_descriptions(self):
        """Show descriptions for all characters"""
        character_descriptions = {
            1: {
                'name': 'Vivienne VanDerBloom',
                'role_hint': 'Elegant socialite with secrets',
                'description': (
                    "- Emphasize how devastated you are, but also that the party must go on.\n"
                    "- Constantly hint that everyone wants your money or status.\n"
                    "- Deny any involvement in the host’s drama — claim they were jealous of your fame."
                ),
                'how_to_play': (
                    "- Be graceful, dramatic, and always slightly superior.\n"
                    "- Use passive-aggressive jabs, especially toward Bianca.\n"
                    "- If accused, respond with flair — like you're too fabulous to be guilty."
                )
            },
            2: {
                'name': 'Casey Penwright',
                'role_hint': 'Ambitious journalist',
                'description': (
                    "- Ask lots of probing questions to deflect suspicion.\n"
                    "- Claim the host was working on a big exposé — but not about you.\n"
                    "- Improvise “scoops” or facts about other characters."
                ),
                'how_to_play': (
                    "- Act like you're constantly investigating a story.\n"
                    "- Stay curious and sly — like you're uncovering the truth.\n"
                    "- Use the line: “I write stories. I don’t star in them.” when under pressure."
                )
            },
            3: {
                'name': 'Bianca Cross',
                'role_hint': 'Mysterious artist',
                'description': (
                    "- Remind everyone you deserved the inheritance.\n"
                    "- Accuse others of jealousy, especially Sebastian and Harper.\n"
                    "- Downplay a past fight with the host — act like it wasn’t serious."
                ),
                'how_to_play': (
                    "- Be theatrical, sarcastic, and dramatic.\n"
                    "- Roll your eyes at Vivienne and act superior.\n"
                    "- Deflect suspicion with humor and flair — “Please. I’d never dirty my heels with crime.”"
                )
            },
            4: {
                'name': 'Sebastian Blackwell',
                'role_hint': 'Wealthy businessman',
                'description': (
                    "- Mention your complicated history with the host, but say it’s personal.\n"
                    "- Deny damaging any art — but be insulted that someone would suggest it.\n"
                    "- Accuse Dante of being too physical to be innocent."
                ),
                'how_to_play': (
                    "- Be mysterious, poetic, and intense — say things like “Pain inspires art.”\n"
                    "- Randomly sketch people as if they inspire you.\n"
                    "- Speak slowly, deliberately — like your every word is profound."
                )
            },
            5: {
                'name': 'Harper Quinn',
                'role_hint': 'Skeptical psychologist',
                'description': (
                    "- Get moody and vague when talking about the host.\n"
                    "- Be suspicious of Nico and mention their closeness to the host.\n"
                    "- Say the host changed over time, and not for the better."
                ),
                'how_to_play': (
                    "- Act introspective and emotionally torn.\n"
                    "- Occasionally slip up — say something you shouldn't, then quickly backtrack.\n"
                    "- Speak as if you’re trying to piece the truth together from memory."
                )
            },
            6: {
                'name': 'Dante Steele',
                'role_hint': 'Charming gambler',
                'description': (
                    "- Mention how protective you were of the host until they stopped listening.\n"
                    "- Say things like “I follow orders. I don’t make kills.”\n"
                    "- Hint you know secrets — especially about Vivienne and Bianca."
                ),
                'how_to_play': (
                    "- Be calm, confident, and a bit menacing.\n"
                    "- Watch others closely like you're always reading them.\n"
                    "- Stay mysterious — let others talk while you drop short, powerful lines."
                )
            },
            7: {
                'name': 'Nico Valentine',
                'role_hint': 'Quiet bookkeeper',
                'description': (
                    "- Act heartbroken — or pretend to be — over the host.\n"
                    "- Deny being obsessed, but react strongly if someone accuses you.\n"
                    "- Drop vague comments about “bedroom secrets.”"
                ),
                'how_to_play': (
                    "- Flirt with others, but keep your sadness close to the surface.\n"
                    "- Cry once (or fake it), then say, “I can’t talk about us… it’s too raw.”\n"
                    "- Be defensive, emotional, and secretive."
                )
            },
            8: {
                'name': 'Mimi Butterfield',
                'role_hint': 'Eccentric heiress',
                'description': (
                    "- Complain about not getting paid by the host.\n"
                    "- Say you saw something while restocking the shrimp.\n"
                    "- Make food puns like “Someone got roasted tonight.”"
                ),
                'how_to_play': (
                    "- Be quirky, nosy, and unpredictable.\n"
                    "- Hand out food like you’re bribing people.\n"
                    "- Laugh off drama and gossip with sass — “Ugh, rich people problems.”"
                )
            }
        }

        while True:
            clear_screen()
            print("=== CHARACTER DESCRIPTIONS ===")
            
            # List all characters
            for char_id, info in character_descriptions.items():
                print(f"\n{char_id}. {info['name']} - {info['role_hint']}")
            
            print("\nSelect a character to view details (1-8)")
            print("or enter 'back' to return to main menu")
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'back' or choice == 'b':
                return
            try:
                char_id = int(choice)
                if 1 <= char_id <= 8:
                    self._show_character_details(character_descriptions[char_id])
                else:
                    print("Please enter 1-8 or 'back'")
            except ValueError:
                print("Please enter a valid number or 'back'")
            
            input("\nPress Enter to continue...")

    def _show_character_details(self, character_info):
        """Show detailed description for one character"""
        clear_screen()
        print(f"=== {character_info['name'].upper()} ===")
        print(f"\nRole Hint: {character_info['role_hint']}")
        print("\nDescription:")
        print(character_info['description'])
        print(f"\nHow To Act:\n{character_info['how_to_play']}")
    
    def _view_murderer_special_clues(self, murderer_id):
        """Show randomized special clues with 2:1 ratio, stored persistently"""
        clear_screen()
        print("=== SECRET MURDERER INTEL ===")
        
        try:
            with self.db.cursor() as c:
                # Get or create murder_clues table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS murder_clues (
                        murderer_id INTEGER,
                        act INTEGER,
                        clue_text TEXT,
                        is_reliable BOOLEAN,
                        PRIMARY KEY (murderer_id, act, clue_text)
                    )
                ''')
                
                # Get co-murderer's ID
                c.execute('SELECT id FROM players WHERE is_murderer=1 AND id!=?', (murderer_id,))
                co_murderer_id = c.fetchone()[0]
                
                # Check if we need to generate new clues
                c.execute('''
                    SELECT COUNT(*) FROM murder_clues 
                    WHERE murderer_id=? AND act<=?
                ''', (murderer_id, self.current_act))
                if c.fetchone()[0] == 0:
                    self._generate_murder_clues(murderer_id, co_murderer_id)
                
                # Display organized by act
                for act in range(1, self.current_act + 1):
                    print(f"\n=== ACT {act} CLUES ===")
                    
                    c.execute('''
                        SELECT clue_text, is_reliable 
                        FROM murder_clues
                        WHERE murderer_id=? AND act=?
                        ORDER BY RANDOM()
                    ''', (murderer_id, act))
                    
                    clues = c.fetchall()
                    for i, (clue, is_reliable) in enumerate(clues, 1):
                        print(f"{i}. {clue}")
                        if not is_reliable and act < self.current_act:
                            print("   (Potentially unreliable information)")
                    
            print("\nNote: Clues are locked in and will persist between sessions")
            input("\nPress Enter to continue...")
            
        except sqlite3.Error as e:
            print(f"\nDatabase error: {str(e)}")
            input("Press Enter to continue...")
    
    def _generate_all_murder_clues(self, murderer_id, co_murderer_id):
        """Generate murder clues with balanced co-murderer bias"""
        try:
            with self.db.cursor() as c:
                # Clear existing clues for this murderer
                c.execute('DELETE FROM murder_clues WHERE murderer_id=?', (murderer_id,))
                
                for act in range(1, 4):  # Acts 1-3
                    # Get all possible clues (excluding murderer's own)
                    c.execute('''
                        SELECT description, character_id
                        FROM clues 
                        WHERE character_id != ? AND act=?
                    ''', (murderer_id, act))
                    
                    all_clues = c.fetchall()
                    
                    if not all_clues:
                        print(f"No clues found for act {act}")
                        continue
                    
                    # Separate co-murderer clues from others
                    co_clues = [row[0] for row in all_clues if row[1] == co_murderer_id]
                    other_clues = [row[0] for row in all_clues if row[1] != co_murderer_id]
                    
                    selected_clues = []
                    
                    # Select 1-2 co-murderer clues (weighted toward 2)
                    num_co_clues = random.choices([1, 2], weights=[30, 70])[0] if len(co_clues) >= 2 else min(1, len(co_clues))
                    selected_clues.extend(random.sample(co_clues, num_co_clues) if co_clues else [])
                    
                    # Fill remaining slots with other clues
                    remaining_slots = 3 - len(selected_clues)
                    if remaining_slots > 0 and other_clues:
                        selected_clues.extend(random.sample(other_clues, min(remaining_slots, len(other_clues))))
                    
                    # Store all clues
                    for clue in selected_clues:
                        c.execute('''
                            INSERT INTO murder_clues 
                            VALUES (?, ?, ?, ?)
                        ''', (murderer_id, act, clue, 1))
        
        except Exception as e:
            print(f"Error generating murder clues: {e}")
            raise
    
    def _view_murderer_special_clues(self, murderer_id):
        """Show randomized special clues with 2:1 ratio, stored persistently"""
        clear_screen()
        print("=== SECRET MURDERER INTEL ===")
        
        try:
            with self.db.cursor() as c:
                # Check if we have any clues for this murderer
                c.execute('SELECT COUNT(*) FROM murder_clues WHERE murderer_id=?', (murderer_id,))
                if c.fetchone()[0] == 0:
                    # Generate new clues if none exist
                    c.execute('SELECT id FROM players WHERE is_murderer=1 AND id!=?', (murderer_id,))
                    co_murderer_id = c.fetchone()[0]
                    self._generate_all_murder_clues(murderer_id, co_murderer_id)
                
                # Display organized by act
                for act in range(1, self.current_act + 1):
                    print(f"\n=== ACT {act} CLUES ===")
                    
                    c.execute('''
                        SELECT clue_text, is_reliable 
                        FROM murder_clues
                        WHERE murderer_id=? AND act=?
                        ORDER BY RANDOM()
                    ''', (murderer_id, act))
                    
                    clues = c.fetchall()
                    if not clues:
                        print("No clues available for this act")
                        continue
                        
                    for i, (clue, is_reliable) in enumerate(clues, 1):
                        print(f"{i}. {clue}")
                        if not is_reliable:
                            print("   (Potentially unreliable information)")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"\nError accessing secret intel: {str(e)}")
            input("Press Enter to continue...")
    
    def _view_murderer_info(self, player_id, name):
        """Show murderer's special role information"""
        clear_screen()
        print(f"=== YOUR ROLE INFO ({name}) ===")
        
        with self.db.cursor() as c:
            # Get co-murderer's name
            c.execute('''
                SELECT name FROM players 
                WHERE is_murderer=1 AND id!=?
            ''', (player_id,))
            co_murderer = c.fetchone()[0]
            
            # Get password
            c.execute('SELECT password FROM players WHERE id=?', (player_id,))
            password = c.fetchone()[0]
        
        print(f"\nYou are: The Murderer")
        print(f"Your Partner: {co_murderer}")
        print(f"Your Password: {password}")
        print("\nSpecial Abilities:")
        print("- See secret murderer-only clues")
        print("- Know your partner's identity")
        print("- Some of your clues are more reliable")
        
        input("\nPress Enter to continue...")
    
    def setup_detective(self, player_id: int, player_name: str):
        """Set up a detective with a password"""
        with self.db.cursor() as c:
            # Clear any existing detective
            c.execute('UPDATE players SET is_detective=0 WHERE is_detective=1')
            
            # Set new detective
            c.execute('''
                UPDATE players 
                SET is_detective=1, is_murderer=0, is_accomplice=0, is_investigator=0, has_completed=1 
                WHERE id=?
            ''', (player_id,))
        
        print("\nAs a detective, create a password:")
        while True:
            password = getpass.getpass("Password (min 4 chars): ")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    with self.db.cursor() as c:
                        c.execute('UPDATE players SET password=? WHERE id=?', (password, player_id))
                    self.detective_id = player_id
                    self.detective_password = password
                    break
            print("Password must be at least 4 characters")
        
        print(f"\n{player_name} registered as detective!")
        input("Press Enter to continue...")

    def setup_investigator(self, player_id: int, player_name: str):
        """Set up an investigator with a password"""
        with self.db.cursor() as c:
            # Clear any existing investigator
            c.execute('UPDATE players SET is_investigator=0 WHERE is_investigator=1')
            
            # Set new investigator
            c.execute('''
                UPDATE players 
                SET is_investigator=1, is_murderer=0, is_accomplice=0, is_detective=0, has_completed=1 
                WHERE id=?
            ''', (player_id,))
        
        print("\nAs an investigator, create a password:")
        while True:
            password = getpass.getpass("Password (min 4 chars): ")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    with self.db.cursor() as c:
                        c.execute('UPDATE players SET password=? WHERE id=?', (password, player_id))
                    self.investigator_id = player_id
                    self.investigator_password = password
                    break
            print("Password must be at least 4 characters")
        
        print(f"\n{player_name} registered as investigator!")
        input("Press Enter to continue...")
    
    def detective_login(self):
        """Handle detective login"""
        clear_screen()
        print("=== DETECTIVE LOGIN ===")
        
        players = self.db.get_players_with_status()
        
        print("\nCharacters:")
        for idx, (player_id, name, _) in enumerate(players, 1):
            print(f"{idx}. {name}")
        
        try:
            choice = int(input("\nSelect your character: ")) - 1
            if 0 <= choice < len(players):
                player_id, name, _ = players[choice]
                
                password = getpass.getpass(f"{name}, enter your password: ")
                
                # Verify password
                with self.db.cursor() as c:
                    c.execute('SELECT password FROM players WHERE id=?', (player_id,))
                    result = c.fetchone()
                    if not result or result[0] != password:
                        print("Incorrect password or character!")
                        input("Press Enter to continue...")
                        return
                
                print(f"\nWelcome back, {name}!")
                self.detective_menu(name)
            else:
                print("Invalid selection!")
        except ValueError:
            print("Please enter a valid number")
        
        input("Press Enter to continue...")

    def investigator_login(self):
        """Handle investigator login"""
        clear_screen()
        print("=== INVESTIGATOR LOGIN ===")
        
        players = self.db.get_players_with_status()
        
        print("\nCharacters:")
        for idx, (player_id, name, _) in enumerate(players, 1):
            print(f"{idx}. {name}")
        
        try:
            choice = int(input("\nSelect your character: ")) - 1
            if 0 <= choice < len(players):
                player_id, name, _ = players[choice]
                
                password = getpass.getpass(f"{name}, enter your password: ")
                
                # Verify password
                with self.db.cursor() as c:
                    c.execute('SELECT password FROM players WHERE id=?', (player_id,))
                    result = c.fetchone()
                    if not result or result[0] != password:
                        print("Incorrect password or character!")
                        input("Press Enter to continue...")
                        return
                
                print(f"\nWelcome back, {name}!")
                self.investigator_menu(name)
            else:
                print("Invalid selection!")
        except ValueError:
            print("Please enter a valid number")
        
        input("Press Enter to continue...")
    
    def detective_menu(self, name: str):
        """Menu for the detective"""
        while True:
            clear_screen()
            print(f"=== DETECTIVE MENU ({name}) ===")
            print("1. View Investigation Clues")
            print("2. View My Role Info")
            print("3. Return to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_detective_clues_weighted()
            elif choice == '2':
                self.view_detective_info()
            elif choice == '3':
                return
            else:
                print("Invalid choice")
                input("Press Enter to continue...")
  
    def investigator_menu(self, name: str):
        """Menu for the investigator"""
        while True:
            clear_screen()
            print(f"=== INVESTIGATOR MENU ({name}) ===")
            print("1. View Innocent Character Hint")
            print("2. View My Role Info")
            print("3. Return to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_innocent_hint()
            elif choice == '2':
                self.view_investigator_info()
            elif choice == '3':
                return
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

    def _generate_investigator_hints(self):
        """Generate and store investigator hints for all acts"""
        with self.db.cursor() as c:
            # Clear existing hints
            c.execute('DELETE FROM investigator_hints')
            
            for act in range(1, 4):  # Acts 1-3
                # Get all non-murderer characters
                c.execute('''
                    SELECT id, name FROM players 
                    WHERE is_murderer=0 AND id!=?
                ''', (self.investigator_id,))
                innocent_chars = c.fetchall()
                
                # Get all murderer characters
                c.execute('SELECT id, name FROM players WHERE is_murderer=1')
                murderer_chars = c.fetchall()
                
                if not innocent_chars:
                    continue
                    
                # Select one character to be the hint for this act
                # 60% chance to show a real innocent, 40% chance to show a murderer
                if random.random() < 0.6:
                    # Show a real innocent
                    char_id, char_name = random.choice(innocent_chars)
                    is_innocent = True
                else:
                    # Show a murderer (false info)
                    if murderer_chars:
                        char_id, char_name = random.choice(murderer_chars)
                        is_innocent = False
                    else:
                        char_id, char_name = random.choice(innocent_chars)
                        is_innocent = True
                
                # Store the hint
                c.execute('''
                    INSERT INTO investigator_hints 
                    VALUES (?, ?, ?, ?)
                ''', (act, char_id, char_name, is_innocent))
        
        self.db.commit()
   
    def view_innocent_hint(self):
        """Show stored investigator hint for current act"""
        clear_screen()
        print("=== INVESTIGATOR'S HINT ===")
        
        with self.db.cursor() as c:
            # Get hint for current act
            c.execute('''
                SELECT character_name, is_innocent 
                FROM investigator_hints 
                WHERE act=?
            ''', (self.current_act,))
            result = c.fetchone()
            
            if not result:
                print("\nNo hint available for current act!")
                input("\nPress Enter to continue...")
                return
                
            char_name, is_innocent = result
            
            print(f"\nYour investigation suggests that {char_name} is NOT a murderer.")
            
            print("\nRemember:\n- Even reliable hints might be misleading!")
            print("- Your hint might ONLY means that person is not a murderer\n- They can still be an accomplice")
        
        input("\nPress Enter to continue...")
  
    def view_detective_info(self):
        """Show the detective's character information"""
        clear_screen()
        print(f"=== YOUR CHARACTER INFO ===")
        
        with self.db.cursor() as c:
            # Get character details
            c.execute('''
                SELECT name, password, is_detective
                FROM players 
                WHERE id=?
            ''', (self.detective_id,))
            result = c.fetchone()
            
        if result:
            print(f"\nCharacter Name: {result['name']}")
            print(f"Your Password: {result['password']}")
            print(f"Role: {'Detective' if result['is_detective'] else 'Unknown'}")
            print("\nSpecial Abilities:")
            print("- See reliability ratings on clues (★ = more reliable)")
            print("- Work with innocents to identify the murderers")
            print("- Your analysis is crucial to solving the case")
            print("\nRemember:")
            print("- Not all clues are equally trustworthy")
            print("- Some reliability rating might be misleading")
            print("- DO NOT share your clues and identity carelessly")
            print("- Murderers and their accomplice could use your informations to identify and help each other")
            print("- Make sure to ONLY share your identity with trusted innocents")
            print("- Murderers may try to mislead you")
        else:
            print("\nError: Character information not found!")
        
        input("\nPress Enter to continue...")

    def view_investigator_info(self):
        """Show the investigator's character information"""
        clear_screen()
        print(f"=== YOUR CHARACTER INFO ===")
        
        with self.db.cursor() as c:
            # Get character details
            c.execute('''
                SELECT name, password, is_investigator
                FROM players 
                WHERE id=?
            ''', (self.investigator_id,))
            result = c.fetchone()
            
        if result:
            print(f"\nCharacter Name: {result['name']}")
            print(f"Your Password: {result['password']}")
            print(f"Role: {'Investigator' if result['is_investigator'] else 'Unknown'}")
            print("\nSpecial Abilities:")
            print("- Get hints about potentially innocent characters")
            print("- 60% chance your information is accurate")
            print("- Your leads can help narrow down suspects")
            print("\nRemember:")
            print("- Verify your information with other trusted players")
            print("- Your info might be intentionally misleading")
            print("- Work with the Detective to solve the case")
            print("- DO NOT share your indentity or clues carelessly")
            print("- Murders and their accomplice might be able to use this to mislead everyone")
        else:
            print("\nError: Character information not found!")
        
        input("\nPress Enter to continue...")
  
    def main_menu(self):
        while True:
            clear_screen()
            print("=== MAIN MENU ===")
            print(f"Game State: {self.game_state} | Current Act: {self.current_act}")
            print("\n1. Player Login")
            print("2. Host Menu")
            print("3. Accomplice Login")
            print("4. Murderer Login")
            print("5. Detective Login")  # New option
            print("6. Investigator Login")  # New option
            print("7. View Character Descriptions")
            print("8. Exit")
            
            choice = input("\nSelect an option: ").strip()
            
            if choice == '1':
                self.player_login()
            elif choice == '2':
                self.host_clue_reveal()
            elif choice == '3':
                self.accomplice_login()
            elif choice == '4':
                self.murderer_login()
            elif choice == '5':
                self.detective_login()
            elif choice == '6':
                self.investigator_login()
            elif choice == '7':
                self.view_character_descriptions()
            elif choice == '8':
                print("Goodbye!")
                sys.exit()
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = ClueGameApp()
    app.main_menu()
