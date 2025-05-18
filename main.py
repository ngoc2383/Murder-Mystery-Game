import os
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
        clear_screen()
        print("=== ACCOMPLICE LOGIN ===")
        
        # Verify accomplice exists
        if not self.accomplice_id:
            print("No accomplice has been set up yet!")
            input("Press Enter to continue...")
            return
        
        # Get accomplice name
        with self.db.cursor() as c:
            c.execute('SELECT name FROM players WHERE id=?', (self.accomplice_id,))
            name = c.fetchone()[0]
        
        # Password verification
        password = getpass.getpass(f"{name}, enter your accomplice password: ")
        if password != self.accomplice_password:
            print("Incorrect password!")
            input("Press Enter to continue...")
            return
        
        # Show accomplice menu
        while True:
            clear_screen()
            print(f"=== ACCOMPLICE MENU ({name}) ===")
            print("1. View Murderers")
            print("2. View Special Clues")
            print("3. Return to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.view_murderers_accomplice()
            elif choice == '2':
                self.view_accomplice_clues()
            elif choice == '3':
                return
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

    def setup_murderer(self, player_id, player_name):
        # Set murderer status
        self.db.set_murderer_status(player_id, True)
        
        # Create collaboration password
        print("\nAs a murderer, create a collaboration password (min 4 chars):")
        while True:
            password = self.authenticate("CREATE PASSWORD")
            if len(password) >= 4:
                if self.confirm_action(f"Confirm password '{password}' is correct?"):
                    self.murderer_passwords[player_id] = password
                    break
            print("Password must be at least 4 characters")
        
        self.db.mark_player_completed(player_id)
        print(f"\nThank you {player_name}. Remember your password!")
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

    def setup_accomplice(self, player_id, player_name):
        # Set as accomplice
        self.accomplice_id = player_id
        
        # Create accomplice password
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

    def view_murderer_collaboration(self):
        clear_screen()
        print("=== MURDERER COLLABORATION ===")
        
        # Show available murderer characters
        with self.db.cursor() as c:
            c.execute('SELECT id, name FROM players WHERE is_murderer=1')
            murderers = c.fetchall()
        
        if not murderers:
            print("No murderers found!")
            input("Press Enter to continue...")
            return
        
        print("\nMurderer characters:")
        for player_id, name in murderers:
            print(f"- {name}")
        
        # Get current player's murderer status
        player_id = input("\nEnter your character number: ").strip()
        try:
            player_id = int(player_id)
            with self.db.cursor() as c:
                c.execute('SELECT is_murderer FROM players WHERE id=?', (player_id,))
                result = c.fetchone()
                
                if not result or not result[0]:
                    print("You are not a murderer!")
                    input("Press Enter to continue...")
                    return
                
                # Verify password
                password = self.authenticate("ENTER COLLABORATION PASSWORD")
                if password != self.murderer_passwords.get(player_id):
                    print("Incorrect password!")
                    input("Press Enter to continue...")
                    return
                
                # Show other murderer
                c.execute('''SELECT name FROM players 
                          WHERE is_murderer=1 AND id!=?''', (player_id,))
                other_murderer = c.fetchone()
                
                if other_murderer:
                    print(f"\nYour co-murderer is: {other_murderer[0]}")
                else:
                    print("\nNo other murderer found yet!")
                
                input("Press Enter to continue...")
                
        except (ValueError, TypeError):
            print("Invalid character number")
            input("Press Enter to continue...")

    def reveal_act_clues(self):
        clear_screen()
        print("=== SELECT CHARACTER FOR CLUES ===")
        
        # Show character list
        players = self.db.get_players_with_status()
        for idx, (player_id, name, completed) in enumerate(players, 1):
            print(f"{idx}. {name}")
        
        try:
            char_choice = int(input("\nSelect character: "))
            if 1 <= char_choice <= len(players):
                selected_id = players[char_choice-1][0]
                self.show_character_clues(selected_id)
            else:
                print(f"Please enter 1-{len(players)}")
                input("Press Enter to continue...")
        except ValueError:
            print("Please enter a number")
            input("Press Enter to continue...")

    def show_character_clues(self, character_id):
        # Get all clue sets for this character
        clue_sets = self.db.get_character_clue_sets(character_id)
        
        while True:
            clear_screen()
            print(f"=== CLUE SETS FOR {self.db.get_character_name(character_id)} ===")
            for set_id, set_num in clue_sets:
                print(f"{set_num}. Set {set_num}")
            print("\n0. Back to character selection")
            
            try:
                set_choice = int(input("\nSelect clue set: "))
                if set_choice == 0:
                    return
                elif any(set_num == set_choice for _, set_num in clue_sets):
                    selected_set = next(set_id for set_id, set_num in clue_sets if set_num == set_choice)
                    self.show_clue_set(selected_set)
                else:
                    print(f"Please enter 0-{len(clue_sets)}")
                    input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number")
                input("Press Enter to continue...")

    def show_clue_set(self, set_id):
        while True:
            clear_screen()
            print("=== SELECT ACT ===")
            print("1. Act 1")
            print("2. Act 2")
            print("3. Act 3")
            print("\n0. Back to set selection")
            
            try:
                act_choice = int(input("\nSelect act: "))
                if act_choice == 0:
                    return
                elif 1 <= act_choice <= 3:
                    clues = self.db.get_clues_for_set_and_act(set_id, act_choice)
                    self.display_clues(clues)
                else:
                    print("Please enter 0-3")
                    input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number")
                input("Press Enter to continue...")

    def display_clues(self, clues):
        clear_screen()
        print("=== CLUES ===")
        for label, desc in clues:
            print(f"\n{label}: {desc}")
        input("\nPress Enter to continue...")

    def get_character_name(self, character_id):
        with self.cursor() as c:
            c.execute('SELECT name FROM players WHERE id=?', (character_id,))
            return c.fetchone()[0]

    def get_clues_for_set_and_act(self, set_id, act):
        with self.cursor() as c:
            c.execute('''SELECT clue_label, description 
                       FROM clues 
                       WHERE set_id=? AND act=?
                       ORDER BY clue_label''', (set_id, act))
            return c.fetchall()

    def host_clue_reveal(self):
        if not self.authenticate("HOST LOGIN", self.host_password):
            print("Invalid host password!")
            input("Press Enter to continue...")
            return
        
        while True:
            clear_screen()
            print("=== HOST MENU ===")
            print("1. Select Act to Reveal Clues")
            print("2. View Murderers (Password Required)")
            print("3. View Accomplice")
            print("4. Reset Options")
            print("5. Back to Main Menu")
            
            choice = input("Select an option: ").strip()
            
            if choice == '1':
                self.reveal_act_clues()
            elif choice == '2':
                if self.authenticate("MURDERER REVEAL", self.host_password):
                    self.view_murderers_host()
            elif choice == '3':
                if self.authenticate("ACCOMPLICE REVEAL", self.host_password):
                    self.view_accomplice()
            elif choice == '4':
                self.reset_options()
            elif choice == '5':
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
            completed_count = sum(1 for _, _, completed in players if completed)
            murderer_count = self.check_murderer_count()
            accomplice_count = 1 if self.accomplice_id else 0
            
            print(f"\nPlayers completed: {completed_count}/8")
            print(f"Murderers selected: {murderer_count}/2")
            print(f"Accomplice selected: {accomplice_count}/1")
            
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
            print("4. Exit")
            
            choice = input("\nSelect an option: ").strip()
            
            if choice == '1':
                self.player_login()
            elif choice == '2':
                self.host_clue_reveal()
            elif choice == '3':
                self.accomplice_login()
            elif choice == '4':
                if self.confirm_action("Are you sure you want to exit?"):
                    print("Goodbye!")
                    sys.exit()
            else:
                print("Invalid choice")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = ClueGameApp()
    app.main_menu()