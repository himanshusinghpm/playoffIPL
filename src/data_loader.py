# data_loader.py
import json
import os

class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.teams = None
        self.standings = None
        self.schedule = None
        self.home_away_stats = None
        self.form_factor = None
        self.historical_thresholds = None
    
    def load_all_data(self):
        """Load all data files"""
        self.teams = self._load_json_file("teams.json")
        self.standings = self._load_json_file("current_standings.json")
        self.schedule = self._load_json_file("schedule.json")
        self.home_away_stats = self._load_json_file("home_away_stats.json")
        self.form_factor = self._load_json_file("form_factor.json")
        
        # Try to load historical thresholds if available
        try:
            self.historical_thresholds = self._load_json_file("historical_thresholds.json")
        except FileNotFoundError:
            self.historical_thresholds = None
        
        return {
            "teams": self.teams,
            "standings": self.standings,
            "schedule": self.schedule,
            "home_away_stats": self.home_away_stats,
            "form_factor": self.form_factor,
            "historical_thresholds": self.historical_thresholds
        }
    
    def _load_json_file(self, filename):
        """Load a JSON file from the data directory"""
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, 'r') as file:
            return json.load(file)
    
    def get_team_by_id(self, team_id):
        """Get team information by ID"""
        if not self.teams:
            self.teams = self._load_json_file("teams.json")
        
        for team in self.teams:
            if team["id"] == team_id:
                return team
        return None
    
    def get_team_by_name(self, team_name):
        """Get team information by full name"""
        if not self.teams:
            self.teams = self._load_json_file("teams.json")
        
        for team in self.teams:
            if team["name"] == team_name:
                return team
        return None
    
    def get_remaining_matches(self):
        """Get matches that haven't been played yet"""
        if not self.schedule:
            self.schedule = self._load_json_file("schedule.json")
        
        return [match for match in self.schedule]
    
    def get_form_factor(self, team_id):
        """Get recent form for a team"""
        if not self.form_factor:
            self.form_factor = self._load_json_file("form_factor.json")
        
        for team in self.form_factor:
            if team["teamId"] == team_id:
                return team["recentForm"]
        return ["N", "N", "N", "N", "N"]  # Default if not found
    
    def get_home_away_stats(self, team_id):
        """Get home/away win rates for a team"""
        if not self.home_away_stats:
            self.home_away_stats = self._load_json_file("home_away_stats.json")
        
        for team in self.home_away_stats:
            if team["teamId"] == team_id:
                return {
                    "homeWinRate": team["homeWinRate"],
                    "awayWinRate": team["awayWinRate"]
                }
        return {"homeWinRate": 0.5, "awayWinRate": 0.5}  # Default if not found