import os, random, getpass, sys
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
        self.accomplice_id = player_id
        
        # Update database
        with self.db.cursor() as c:
            # First clear any existing accomplice
            c.execute('UPDATE players SET is_accomplice=0')
            # Set new accomplice
            c.execute('UPDATE players SET is_accomplice=1 WHERE id=?', (player_id,))
        self.db.commit()
        
        print("\nAs an accomplice, create a password to view murderers:")
        while True:
            password = self.authenticate("CREATE PASSWORD")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    self.accomplice_password = password
                    break
            print("Password must be at least 4 characters")
        
        self.db.mark_player_completed(player_id)
        print(f"\nThank you {player_name}. Remember your password!")
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
        """Menu for logged-in murderer"""
        while True:
            clear_screen()
            print(f"=== MURDERER MENU ({name}) ===")
            print("1. View Co-Murderer")
            print("2. View Special Clues")
            print("3. Logout")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_co_murderer(player_id)
            elif choice == '2':
                self.view_murderer_clues(player_id)
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
                self.db.set_murderer_status(player_id, False)
                self.db.mark_player_completed(player_id)
                print(f"\n{player_name} registered as innocent.")
                input("Press Enter to continue...")
                break
            
            elif choice == "2":
                '''
                # Only check murderer count if we're setting a new murderer
                if self.check_murderer_count() >= 2:
                    print(f"\n{player_name} cannot be a murderer.")
                    print("Maximum 2 murderers already selected.")
                    print("Please choose another role.")
                    input("Press Enter to continue...")
                    continue
                '''
                if self.confirm_action(f"Confirm {player_name} is a murderer?"):
                    self.setup_murderer(player_id, player_name)
                    break
            
            elif choice == "3":
                if self.accomplice_id:
                    print("\nAn accomplice has already been selected!")
                    print("Please choose another role.")
                    input("Press Enter to continue...")
                    continue
                
                if self.confirm_action(f"Confirm {player_name} is the accomplice?"):
                    self.setup_accomplice(player_id, player_name)
                    break
            
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

    def check_roles_setup(self):
        """Verify roles are properly assigned (only called once)"""
        clear_screen()
        print("=== ROLES VERIFICATION ===")
        
        murderer_count = self.check_murderer_count()
        accomplice_count = 1 if self.accomplice_id else 0
        
        issues_found = False
        
        if murderer_count != 2:
            print(f"\nWARNING: {murderer_count} murderer(s) selected (need exactly 2)!")
            issues_found = True
        
        if accomplice_count != 1:
            print(f"\nWARNING: {accomplice_count} accomplice(s) selected (need exactly 1)!")
            issues_found = True
        
        if not issues_found:
            print("\nAll roles properly assigned!")
            print("- 2 murderers selected")
            print("- 1 accomplice selected")
            self.game_state = "READY"
            # Initialize game clues only once
            self._select_final_clues_for_acts()
            print("\nGame clues have been initialized!")
        else:
            print("\nRole setup incomplete!")
        
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
        """Advance to the next act"""
        if self.current_act >= 3:
            print("\nGame completed! All acts finished.")
            self.game_state = "COMPLETED"
        else:
            self.current_act += 1
            print(f"\nAdvanced to Act {self.current_act}!")
        
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
            print("=== HOST MENU ===")
            print(f"Game State: {self.game_state} | Current Act: {self.current_act}")
            print("1. Reveal Current Act Clues")
            print("2. View Murderers")
            print("3. View Accomplice")
            print("4. Reset Options")
            print("5. Advance Act")
            print("6. Back to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.display_act_clues(self.current_act)
            elif choice == '2':
                self.view_murderers_host()
            elif choice == '3':
                self.view_accomplice()
            elif choice == '4':
                self.reset_options()
            elif choice == '5':
                self.advance_act()  # No state check needed
            elif choice == '6':
                return
            else:
                print("Invalid choice. Please try again.")
                input("Press Enter to continue...")  
    
    def main_menu(self):
        while True:
            clear_screen()
            print("=== MAIN MENU ===")
            players = self.db.get_players_with_status()
            completed_count = sum(1 for _, _, completed in players if completed)
            
            print(f"Players: {completed_count}/8 | State: {self.game_state} | Act: {self.current_act}")
            
            print("\n1. Player Login")
            print("2. Host Menu")
            print("3. Accomplice Login")
            print("4. Murderer Login")
            print("5. Exit")
            
            choice = input("\nSelect an option: ").strip()
            print("3. Accomplice Login")
            print("4. Murderer Login")
            print("5. Exit")

            if choice == '1':
                self.player_login()
            elif choice == '2':
                self.host_clue_reveal()
            elif choice == '3':
                self.accomplice_login()
            elif choice == '4':
                self.murderer_login()
            elif choice == '5':
                if self.confirm_action("Are you sure you want to exit?"):
                    print("Goodbye!")
                    sys.exit()
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = ClueGameApp()
    app.main_menu()