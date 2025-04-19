# elo_calculator.py
class EloCalculator:
    def __init__(self, standings, form_factor, home_away_stats):
        self.standings = standings
        self.form_factor = form_factor
        self.home_away_stats = home_away_stats
        self.ratings = self._initialize_elo_ratings()
    
    def _initialize_elo_ratings(self):
        """Initialize ELO ratings based on current standings and other factors"""
        # Start with base rating of 1500 for all teams
        ratings = {}
        team_ids = set()
        
        # Get all team IDs from standings
        for team in self.standings:
            team_ids.add(team["team"])
        
        # Initialize all teams with base rating
        for team_id in team_ids:
            ratings[team_id] = 1500
        
        # Adjust based on current season performance
        for team in self.standings:
            team_id = team["team"]
            
            # Points adjustment (more points = higher rating)
            ratings[team_id] += team["points"] * 15
            
            # NRR adjustment
            ratings[team_id] += team["nrr"] * 50
            
            # Form factor adjustment
            form_bonus = self._calculate_form_bonus(team_id)
            ratings[team_id] += form_bonus
            
            # Win percentage adjustment
            if team["played"] > 0:
                win_percentage = team["wins"] / team["played"]
                # Adjust rating based on win percentage (centered at 0.5)
                ratings[team_id] += (win_percentage - 0.5) * 100
        
        return ratings
    
    def _calculate_form_bonus(self, team_id):
        """Calculate bonus based on recent form"""
        form = None
        
        # Find team in form factor data
        for team in self.form_factor:
            if team["teamId"] == team_id:
                form = team["recentForm"]
                break
        
        if not form:
            return 0
        
        # Calculate bonus based on recent results
        # More recent matches have higher weight
        form_bonus = 0
        weights = [1, 0.8, 0.6, 0.4, 0.2]  # Most recent match has highest weight
        
        for i, result in enumerate(form):
            if i >= len(weights):
                break
            
            if result == "W":
                form_bonus += 10 * weights[i]
            elif result == "L":
                form_bonus -= 5 * weights[i]
            # No change for "N" (no result)
        
        return form_bonus
    
    def get_ratings(self):
        """Get all team ELO ratings"""
        return self.ratings
    
    def get_team_rating(self, team_id):
        """Get ELO rating for a specific team"""
        return self.ratings.get(team_id, 1500)  # Default 1500 if not found
    
    def calculate_win_probability(self, home_team, away_team):
        """Calculate win probability based on ELO ratings"""
        home_rating = self.get_team_rating(home_team)
        away_rating = self.get_team_rating(away_team)
        
        # Apply home advantage
        home_advantage = 0
        
        # Find home team's home win rate
        for team in self.home_away_stats:
            if team["teamId"] == home_team:
                # Scale home advantage by how much better the team performs at home
                home_advantage = (team["homeWinRate"] - 0.5) * 100
                break
        
        # Add home advantage (minimum 30 points)
        adjusted_home_rating = home_rating + max(30, home_advantage)
        
        # Calculate probability using ELO formula
        exp_home = 1 / (1 + 10 ** ((away_rating - adjusted_home_rating) / 400))
        return exp_home
    
    def update_ratings(self, home_team, away_team, home_team_won, k_factor=32):
        """Update ELO ratings after a match"""
        # Get current ratings
        home_rating = self.get_team_rating(home_team)
        away_rating = self.get_team_rating(away_team)
        
        # Get expected outcome
        expected_home = self.calculate_win_probability(home_team, away_team)
        expected_away = 1 - expected_home
        
        # Actual outcome
        actual_home = 1 if home_team_won else 0
        actual_away = 1 - actual_home
        
        # Update ratings
        new_home_rating = home_rating + k_factor * (actual_home - expected_home)
        new_away_rating = away_rating + k_factor * (actual_away - expected_away)
        
        # Update ratings dictionary
        self.ratings[home_team] = new_home_rating
        self.ratings[away_team] = new_away_rating
        
        return {
            home_team: new_home_rating,
            away_team: new_away_rating
        }