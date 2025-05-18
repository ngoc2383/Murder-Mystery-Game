import os, random
import getpass
import sys
from database import ClueData

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
        with self.db.cursor() as c:
            c.execute('UPDATE players SET is_murderer=NULL, has_completed=0')
        self.murderer_passwords = {}
        print("\nAll player logins have been reset!")
        input("Press Enter to continue...")

    def reset_single_player(self, player_id):
        with self.db.cursor() as c:
            c.execute('UPDATE players SET is_murderer=NULL, has_completed=0 WHERE id=?', (player_id,))
        self.murderer_passwords.pop(player_id, None)
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

    def setup_accomplice(self, player_id, player_name):
        """Set up accomplice with password"""
        self.accomplice_id = player_id
        
        print(f"\n{player_name}, create your accomplice password (min 4 chars):")
        while True:
            password = getpass.getpass("Password: ")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    # Store password in database
                    with self.db.cursor() as c:
                        c.execute('UPDATE players SET password=?, is_accomplice=1 WHERE id=?', 
                                (password, player_id))
                    self.db.mark_player_completed(player_id)
                    print(f"\nPassword set! Remember it, {player_name}!")
                    input("Press Enter to continue...")
                    break
            else:
                print("Password must be at least 4 characters")

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
        clear_screen()
        print("=== ROLES VERIFICATION ===")
        
        murderer_count = self.check_murderer_count()
        accomplice_count = 1 if self.accomplice_id else 0
        issues_found = False
        
        if murderer_count != 2:
            print(f"\nWARNING: {murderer_count} murderer(s) selected (need exactly 2)!")
            issues_found = True
        
        if accomplice_count > 1:
            print(f"\nWARNING: {accomplice_count} accomplices selected (max 1 allowed)!")
            issues_found = True
        elif accomplice_count < 1:
            print("\nWARNING: No accomplice selected!")
            issues_found = True
        
        if not issues_found:
            print("\nAll roles properly assigned!")
            print("- 2 murderers selected")
            print("- 1 accomplice selected")
        
        input("\nPress Enter to continue...")

    def prepare_clue_pools(self):
        """Assign random clue sets (1-3) to each character"""
        with self.db.cursor() as c:
            # Assign random clue sets to each character (stored in has_completed field)
            for char_id in range(1, 9):
                set_number = random.randint(1, 3)
                c.execute("UPDATE players SET has_completed=? WHERE id=?", (set_number, char_id))

    def get_weighted_clues(self, act):
        """Get all clues for current act with weights based on murderer status"""
        with self.db.cursor() as c:
            c.execute('''
                SELECT c.description, p.is_murderer
                FROM clues c
                JOIN players p ON c.character_id = p.id
                WHERE c.act = ? 
                AND c.set_number = p.has_completed
            ''', (act,))
            
            clues = []
            for description, is_murderer in c.fetchall():
                # Assign higher weight to murderer's clues (3x)
                weight = 3 if is_murderer else 1
                clues.append((description, weight))
            
            return clues

    def reveal_act_clues(self):
        """Host interface for revealing clues for current act"""
        clear_screen()
        print(f"=== ACT {self.current_act} CLUES ===")
        
        # Get and display 3 weighted clues
        clues = self.select_clues_for_act(self.current_act)
        
        if not clues:
            print("No clues found for this act!")
            input("Press Enter to continue...")
            return
        
        print("\nSelected clues for this act:")
        for i, clue in enumerate(clues[:3], 1):  # Ensure exactly 3 clues
            # Clean up clue display by removing set info
            clean_clue = clue.split(' - Act ')[0]  # Just show character and clue
            print(f"{i}. {clean_clue}")
        
        # Show which characters these clues came from (without set info)
        print("\nClue origins:")
        with self.db.cursor() as c:
            for clue in clues[:3]:
                # Extract base clue info for lookup
                base_clue = clue.split(' - Act')[0]
                c.execute('''
                    SELECT p.name 
                    FROM clues c
                    JOIN players p ON c.character_id = p.id
                    WHERE c.description LIKE ? 
                    AND c.act = ?
                    LIMIT 1
                ''', (f"{base_clue}%", self.current_act))
                result = c.fetchone()
                if result:
                    print(f"- From {result[0]}'s clues")
        
        input("\nPress Enter to continue...")

    def select_clues_for_act(self, act):
        """Select 3 clues for specified act using weighted random selection"""
        weighted_clues = self.get_weighted_clues(act)
        
        if not weighted_clues:
            return []
        
        # Extract clues and weights
        clues, weights = zip(*weighted_clues)
        
        # Select 3 unique clues with weighted probability
        selected = []
        while len(selected) < 3 and len(clues) > 0:
            # Get one random clue
            new_clue = random.choices(clues, weights=weights, k=1)[0]
            
            # Add if not already selected
            if new_clue not in selected:
                selected.append(new_clue)
            
            # Prevent infinite loops if not enough unique clues
            if len(selected) == len(clues):
                break
        
        return selected[:3]  # Return exactly 3 clues
    def advance_act(self):
        """Move to the next act"""
        if self.current_act < 3:
            self.current_act += 1
            print(f"\nAdvanced to Act {self.current_act}")
        else:
            print("\nThis is the final act!")
        input("Press Enter to continue...")

    def reset_options(self):
        """Reset game options while preserving player roles"""
        clear_screen()
        print("=== RESET OPTIONS ===")
        print("1. Reset All Clue Assignments")
        print("2. Reset Current Act")
        print("3. Reset Player Checkin")
        print("4. Back to Host Menu")
        
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
            if self.confirm_action("Reset all player check-ins/logins?"):
                with self.db.cursor() as c:
                    # Reset has_completed flag but keep roles
                    c.execute('UPDATE players SET has_completed=0')
                print("\nAll player check-ins/logins have been reset!")
        elif choice == '4':
            return
        else:
            print("Invalid choice")
        
        input("Press Enter to continue...")

    def host_clue_reveal(self):
        if not self.authenticate("HOST LOGIN", self.host_password):
            print("Invalid host password!")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print("=== HOST MENU ===")
            print(f"Current Act: {self.current_act}")
            print("1. Reveal Clues for Current Act")
            print("2. Advance to Next Act")
            print("3. View Murderers")
            print("4. View Accomplice")
            print("5. Reset Options")
            print("6. Back to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.reveal_act_clues()
            elif choice == '2':
                self.advance_act()
            elif choice == '3':
                if self.authenticate("MURDERER REVEAL", self.host_password):
                    self.view_murderers_host()
            elif choice == '4':
                if self.authenticate("ACCOMPLICE REVEAL", self.host_password):
                    self.view_accomplice()
            elif choice == '5':
                self.reset_options()
            elif choice == '6':
                return
            else:
                print("Invalid choice. Please try again.")
                input("Press Enter to continue...")

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

    def main_menu(self):
        while True:
            clear_screen()
            print("=== MAIN MENU ===")
            
            # Show current game setup status
            players = self.db.get_players_with_status()
            murderer_count = self.check_murderer_count()
            accomplice_count = 1 if self.accomplice_id else 0
            
            # Show warnings if all players completed
            if all(completed for _, _, completed in players):
                if murderer_count != 2:
                    print("\nWARNING: Need exactly 2 murderers!")
                if accomplice_count > 1:
                    print("WARNING: More than 1 accomplice selected!")
                elif accomplice_count < 1:
                    print("WARNING: No accomplice selected!")
            
            print("\n1. Player Login")
            print("2. Host Menu")
            print("3. Accomplice Login")
            print("4. Murderer Login")
            print("5. Exit")
            
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
                if self.confirm_action("Are you sure you want to exit?"):
                    print("Goodbye!")
                    sys.exit()
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = ClueGameApp()
    app.main_menu()