#Ali Kamaly | DEAD PULSE
#Stats Manager Class

import json
"""
Using JSON for data storage provides several key advantages:

--> JSON makes future expansion of DEAD PULSE significantly easier by allowing new data/features to be added seamlessly
--> JSON files store data in a human-readable structured format that is easy to read and modify manually if needed
--> Persistence Across Sessions: Unlike in-memory storage, JSON allows data to be saved and reloaded across different gaming sessions
--> Flexibility & Scalability: JSON supports nested structures, making it easy to store complex data such as player stats, 
game performance, and previous game saves
--> Error Handling & Robustness: With exception handling for file reading and writing, JSON storage ensures that game data remains
intact and prevents data loss from unexpected crashes


In DEAD PULSE, JSON is used to:
 - Maintain records of all player accounts in a structured and efficient manner
 - Store and update player stats persistently i.e.(permanently) allowing players to be competitive amongst one another
 for the highest number of zombies killed or wave highscore
 - Save and load previous game states to allow users to continue from the wave where they left off allowing for game progression
"""

class StatsManager():

    """
    Manages everything to do with player stats and data i.e. updating, deleting saving
    Efficiently saves player progress between sessions, including detailed wave information 
    (such as zombie counts, zombie stat multipliers, and time allocated) while preventing data loss 
    via robust error handling for missing files or corrupt data

    By using JSON, the system remains human-readable for debugging while supporting future expansion
    """    


    def __init__(self, username= None, file_name = "Data/player_data.json"):
        self.file = file_name
        self.username = username
        self.all_player_stats = {}
        #by default stats would be empty
        if username:
            self.load_stats()
        else:
            self.load_all_stats()

    def load_stats(self):
        """Loads stats of a specific player"""
        try:
            with open(self.file, "r") as file:
                data = json.load(file)
                if self.username in data:
                    self.player_stats = data[self.username]["Stats"]
                    #print("User already exists")
                else:
                    #username was not used before so create new user instead of loading data
                    #with default stat values i.e. health = 100, bullets fired = 0
                    self._create_new_user()
                    #print("Username Doesn't Exist")
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            #keyerror occurs when creating a new user in database
            data = {}
            self._create_new_user()
            #protective programming - just in case no stats file is found, new user is created
        
        self.save_stats()
    
    def load_all_stats(self):
        """Loads stats of all players"""
        """Actually loads every single data in json file"""
        try:
            with open(self.file, "r") as file:
                self.all_player_stats = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.all_player_stats = {}
            #print("Couldn't access all the data- returned empty all player stats dictionary")

    def get_all_stats(self):
        """Returns every single piece of data that is stored in the json file"""
        return self.all_player_stats

    def _create_new_user(self):
        """Creates new user with default stat values"""
        self.player_stats = {
            "Total Zombies Killed": 0,
            "Total Bullets Fired": 0,
            "Total Bullets Hit": 0,
            "Total Waves Survived": 0,
            "Wave Highscore": 0,
            "Rotten Flesh": 0,
            "Total Score": 0,
            "Max Health": 100,
            "Attack Damage": 5
        }
        #print("new user created")

    def increment_stat(self, stat, increment = 1):
        if stat in self.player_stats:
            self.player_stats[stat]+= increment
        #where stat is a piece of data being stored i.e. Total Zombies Killed

    def _set_stat(self, stat, value):
        """Should only ever be called by the program"""
        if stat in self.player_stats:
            self.player_stats[stat] = value

    def update_wave_highscore(self,wave_number):
        if wave_number> self.player_stats["Wave Highscore"]:
            self.player_stats["Wave Highscore"] = wave_number

    def save_game(self, game_state):
        """Saves the game at the beginning of each new wave"""

        self.load_all_stats()

        if game_state.game_over:
            return
            #doesn't save if player has died (nothing to save)
        #saves all the necessary game data to reload again at a later point in time
        self.all_player_stats[self.username]["Previous Game"] = {
            "Wave Number": game_state.wave_number,
            "Health": game_state.player.health_bar.current_health,
            "Heart Rate": game_state.player.heart.current_heart_rate,
            "Ammo": game_state.player.ammo,
            "Battery": game_state.field_of_view.get_radius(),
            "Walkers": game_state.walker_count,
            "Runners": game_state.runner_count,
            "Brutes": game_state.brute_count,
            "Batteries Spawned": game_state.battery_spawn_count,
            "Bullets Spawned": game_state.bullet_spawn_count,
            "Medkits Spawned": game_state.medkit_spawn_count,
            "Zombie Health Multiplier": game_state.zombie_health_multiplier,
            "Zombie Attack Multiplier": game_state.zombie_attack_multiplier,
            "Time Allocated": game_state.timer.duration,
            "Map": game_state.current_map,
            "Game Performance": game_state.saved_player_performance | game_state.overall_player_performance
            #combining the two dictionaries together (saved performance + new performance)
        }
        #print("saving game")
        self.save_data()

    def saved_game_avaiable(self):
        """Checks if player has a previously saved game avaiable to load"""
        self.load_all_stats()
        if "Previous Game" in self.all_player_stats[self.username]:
            return True
        return False
    
    def get_saved_game_data(self):
        """Returns all the saved previous game data"""
        return self.all_player_stats[self.username]["Previous Game"]

    def get_game_performance(self):
        return self.all_player_stats[self.username]["Previous Game"]["Game Performance"]

        
    def delete_previous_game_save(self):
        """
        Deletes saved game as player has died and so there is nothing to load - player must
        start again if they want to play again
        """

        self.load_all_stats()
        try:
            del self.all_player_stats[self.username]["Previous Game"]

            self.save_data()
            #print("Previous game deleted cause u died")
        except KeyError:
            print("KeyError the username isn't part of all_player_stats. Didn't delete previous game")

    def save_data(self):
        """Dumps updated player data to JSON file"""

        with open(self.file, 'w') as file:
            json.dump(self.all_player_stats, file, indent = 4)

        #print("data saved to json file now")

    def save_stats(self):
        """
        Data is read from player stats and is stored. Only stats related to curernt player i.e. zombies killed is edited.
        Then the data is dumped back into the json file
        """
        try: 
            with open (self.file, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
            print("Error returned empty dictionary instead")
        

        if self.username not in data:
            data[self.username] = {"Stats": {}}

        #making sure stats is saved inside the user's data as a dictionary
        if "Stats" not in data[self.username]:
            data[self.username]["Stats"] = {}

        #only updating stat that has been updated
        data[self.username]["Stats"].update(self.player_stats)
        
        with open(self.file, "w") as file:
            json.dump(data, file, indent = 4)
            #rewrites the whole json file with new updated data
        #print("stats now saved")
