import os, random, getpass, sys, sqlite3
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
        self.current_act = 1
        self.game_state = "WAITING"
        
        # Initialize murder_clues table
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

        self.current_act, self.game_state = self.db.load_game_state()
   
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
            c.execute('UPDATE players SET is_murderer=NULL, is_accomplice=0, has_completed=0')
        self.murderer_passwords = {}
        self.accomplice_id = None
        self.accomplice_password = None
        self.db.commit()
        print("\nAll player logins have been reset!")
        input("Press Enter to continue...")

    def reset_single_player(self, player_id: int):
        """Reset a single player's login status"""
        with self.db.cursor() as c:
            c.execute('UPDATE players SET is_murderer=NULL, is_accomplice=0, has_completed=0 WHERE id=?', (player_id,))
        self.murderer_passwords.pop(player_id, None)
        if player_id == self.accomplice_id:
            self.accomplice_id = None
            self.accomplice_password = None
        self.db.commit()
        print("\nPlayer login has been reset!")
        input("Press Enter to continue...")
    
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
                # Only show verification if explicitly accessed through host menu
                if self.game_state == "WAITING":
                    self.check_roles_setup()
                return
            
            try:
                choice = input("\nEnter character number (or 'back'): ").strip()
                if choice.lower() == 'back':
                    return
                
                choice = int(choice)
                if 1 <= choice <= len(players):
                    selected_id, selected_name, completed = players[choice-1]
                    if completed:
                        print("This character has already completed login!")
                        input("Press Enter to continue...")
                        continue
                    
                    self.handle_role_selection(selected_id, selected_name)
                    break
                
                print(f"Please enter 1-{len(players)} or 'back'")
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number or 'back'")
                input("Press Enter to continue...")

    def handle_role_selection(self, player_id, player_name):
        while True:
            clear_screen()
            print(f"=== ROLE SELECTION ({player_name}) ===")
            print("1. Innocent")
            print("2. Murderer") 
            print("3. Accomplice")
            
            choice = input("Select role: ").strip()
            
            if choice == "1":
                with self.db.cursor() as c:
                    c.execute('''
                        UPDATE players 
                        SET is_murderer=0, is_accomplice=0, has_completed=1
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
                            SET is_murderer=1, is_accomplice=0, has_completed=1
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
                    
            else:
                print("Invalid choice")
                input("Press Enter to continue...")
   
    def check_roles_setup(self):
        """Verify roles and generate all murder clues when game becomes ready"""
        clear_screen()
        print("=== ROLES VERIFICATION ===")
        
        murderer_count = self.check_murderer_count()
        accomplice_count = 1 if self.accomplice_id else 0
        
        if murderer_count == 2 and accomplice_count == 1:
            print("\nAll roles properly assigned!")
            self.game_state = "READY"
            
            # Generate ALL murder clues (acts 1-3) upfront
            with self.db.cursor() as c:
                c.execute('SELECT id FROM players WHERE is_murderer=1')
                murderers = [row[0] for row in c.fetchall()]
                
                for murderer_id in murderers:
                    c.execute('SELECT id FROM players WHERE is_murderer=1 AND id!=?', (murderer_id,))
                    co_murderer_id = c.fetchone()[0]
                    self._generate_all_murder_clues(murderer_id, co_murderer_id)
            
            print("Murderer intel has been prepared for all acts!")
            self.db.save_game_state(self.current_act, self.game_state)
        else:
            print("\nWARNING: Role setup incomplete!")
        
        input("\nPress Enter to continue...")
    
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
        """Select and store final clues for all acts using weighted selection"""
        with self.db.cursor() as c:
            # Clear any existing game clues
            c.execute('DELETE FROM game_clues')
            
            for act in range(1, 4):  # Acts 1-3
                clues = self._select_weighted_clues(act)
                c.execute('''
                    INSERT INTO game_clues (act, clue1, clue2, clue3)
                    VALUES (?, ?, ?, ?)
                ''', (act, *clues))
        self.db.commit()

    def _select_weighted_clues(self, act: int) -> List[str]:
        """Select 3 clues for an act with murderer weighting"""
        with self.db.cursor() as c:
            c.execute('''
                SELECT c.description, 
                    CASE WHEN p.is_murderer=1 THEN 3 ELSE 1 END as weight
                FROM clues c
                JOIN players p ON c.character_id = p.id
                WHERE c.act = ? 
                AND c.set_number = p.has_completed
            ''', (act,))
            weighted_clues = c.fetchall()
        
        if not weighted_clues:
            return ["No clues available"] * 3
        
        # Convert to separate lists for random.choices
        clues = [row[0] for row in weighted_clues]
        weights = [row[1] for row in weighted_clues]
        
        # Select 3 unique clues with weighting
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
            if self.confirm_action("Reset all clue set assignments?"):
                self.prepare_clue_pools()
                print("\nClue sets have been randomly reassigned!")
        elif choice == '2':
            if self.confirm_action("Reset current act to Act 1?"):
                self.current_act = 1
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

    def check_roles_setup(self):
        """Manual role verification"""
        clear_screen()
        print("=== ROLES VERIFICATION ===")
        
        murderer_count = self.check_murderer_count()
        accomplice_count = 1 if self.accomplice_id else 0
        
        print(f"\nCurrent Status:")
        print(f"- Murderers: {murderer_count}/2")
        print(f"- Accomplice: {accomplice_count}/1")
        
        if murderer_count == 2 and accomplice_count == 1:
            print("\nAll roles properly assigned!")
            self.game_state = "READY"
            if not self._game_clues_exist():  # Only initialize if needed
                self._select_final_clues_for_acts()
                print("\nGame clues initialized!")
        else:
            print("\nWARNING: Role setup incomplete!")
            print("Please complete role assignments through Player Login")
        
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
                if self.authenticate("HOST VERIFICATION", self.host_password):
                    self.restart_game()
            elif choice == '7':
                return
            else:
                print("Invalid choice. Please try again.")
                input("Press Enter to continue...")
   
    def restart_game(self):
        """Completely reset all game data and tables including murder_clues"""
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
                # Drop all game tables including murder_clues
                c.execute('DROP TABLE IF EXISTS players')
                c.execute('DROP TABLE IF EXISTS clues')
                c.execute('DROP TABLE IF EXISTS game_clues')
                c.execute('DROP TABLE IF EXISTS murder_clues')  # New line
                
                # Reinitialize database
                self.db._initialize_db()
                self.db._seed_characters()
                self.db._seed_clues()
                
                # Recreate murder_clues table structure
                c.execute('''
                    CREATE TABLE IF NOT EXISTS murder_clues (
                        murderer_id INTEGER,
                        act INTEGER,
                        clue_text TEXT,
                        is_reliable BOOLEAN,
                        PRIMARY KEY (murderer_id, act, clue_text)
                    )
                ''')
                
                # Reset all game state
                self.murderer_passwords = {}
                self.accomplice_password = None
                self.accomplice_id = None
                self.current_act = 1
                self.game_state = "WAITING"
                
            print("\nGame completely reset! All data erased.")
            print("New game ready to be set up.")
        except Exception as e:
            print(f"\nError resetting game: {str(e)}")
            # Ensure tables exist even if error occurs
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
        
        input("Press Enter to continue...")
    
    def accomplice_menu(self, name: str):
        """Special menu for the accomplice with weighted clues"""
        while True:
            clear_screen()
            print(f"=== ACCOMPLICE MENU ({name}) ===")
            print("1. View Special Clues")
            print("2. View My Character Info")
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
        """Get the same 3 game clues but with reliability ratings"""
        with self.db.cursor() as c:
            # Get the standard 3 game clues for this act
            c.execute('SELECT clue1, clue2, clue3 FROM game_clues WHERE act=?', (act,))
            game_clues = c.fetchone()
            
            if not game_clues:
                return []
                
            # Get reliability weights for each clue
            weighted_clues = []
            for clue in [game_clues['clue1'], game_clues['clue2'], game_clues['clue3']]:
                # Extract character name from clue string (format: "Name - Clue - Act X - Set Y")
                try:
                    character_name = clue.split(' - ')[0].strip()
                except:
                    # Fallback if clue format is different
                    weighted_clues.append((clue, 1))  # Default weight
                    continue
                    
                # Get weight for this character's clue
                c.execute('''
                    SELECT 
                        CASE 
                            WHEN is_murderer=1 THEN 3  -- Highest weight for murderers
                            WHEN id=? THEN 2           -- Medium weight for accomplice's own clues
                            ELSE 1                     -- Low weight for others
                        END as weight
                    FROM players 
                    WHERE name=?
                ''', (self.accomplice_id, character_name))
                
                result = c.fetchone()
                weight = result['weight'] if result else 1
                weighted_clues.append((clue, weight))
                
            return weighted_clues
  
    def view_accomplice_clues_weighted(self):
        """Show standard 3 game clues with reliability ratings"""
        clear_screen()
        print(f"=== YOUR SPECIAL CLUES (ACT {self.current_act}) ===")
        
        clues = self._get_weighted_accomplice_clues(self.current_act)
        
        if not clues:
            print("\nNo clues available for current act!")
            input("Press Enter to continue...")
            return
        
        print("\nThe same clues everyone sees, but you know which might be trustworthy:")
        for i, (clue, weight) in enumerate(clues, 1):
            print(f"\n{i}. {clue}")
            print(f"   Reliability: {'★' * weight}{'☆' * (3-weight)}")
        
        print("\nRemember: Even highly-rated clues might be misleading!")
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
            
            if choice == 'back':
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
        """Generate murder clues for all acts (1-3) upfront"""
        with self.db.cursor() as c:
            # Clear any existing clues for this murderer
            c.execute('DELETE FROM murder_clues WHERE murderer_id=?', (murderer_id,))
            
            for act in range(1, 4):  # Generate for all 3 acts
                # Get 2 reliable clues from co-murderer
                c.execute('''
                    SELECT description FROM clues 
                    WHERE character_id=? AND act=?
                    ORDER BY RANDOM() LIMIT 2
                ''', (co_murderer_id, act))
                reliable_clues = [(row[0], 1) for row in c.fetchall()]
                
                # Get 1 unreliable clue from innocents
                c.execute('''
                    SELECT description FROM clues
                    WHERE character_id NOT IN (?,?) AND act=?
                    ORDER BY RANDOM() LIMIT 1
                ''', (murderer_id, co_murderer_id, act))
                unreliable_clue = [(row[0], 0) for row in c.fetchall()]
                
                # Store all clues
                for clue_text, is_reliable in reliable_clues + unreliable_clue:
                    c.execute('''
                        INSERT INTO murder_clues 
                        VALUES (?, ?, ?, ?)
                    ''', (murderer_id, act, clue_text, is_reliable))
        
        self.db.commit()
   
    def _view_murderer_special_clues(self, murderer_id):
        """Show pre-generated murder clues for current/previous acts"""
        clear_screen()
        print("=== SECRET MURDERER INTEL ===")
        
        try:
            with self.db.cursor() as c:
                # Display clues for each available act
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
                
            print(f"\nIntel prepared through Act {self.current_act}")
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
   
    def main_menu(self):
        while True:
            clear_screen()
            print("=== MAIN MENU ===")
            print(f"Game State: {self.game_state} | Current Act: {self.current_act}")
            print("\n1. Player Login")
            print("2. Host Menu")
            print("3. Accomplice Login")
            print("4. Murderer Login")
            print("5. View Character Descriptions")  # New option
            print("6. Exit")
            
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
                self.view_character_descriptions()  # New function
            elif choice == '6':
                print("Goodbye!")
                sys.exit()
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = ClueGameApp()
    app.main_menu()