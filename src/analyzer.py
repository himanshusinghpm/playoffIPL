# analyzer.py
class PlayoffsAnalyzer:
    def __init__(self, simulation_results, standings, teams):
        self.results = simulation_results
        self.standings = standings
        self.teams = teams
    
    def get_qualification_probabilities(self):
        """Get qualification probabilities sorted by probability"""
        probs = self.results["qualification_probability"]
        
        # Convert to list of (team, prob) tuples and sort
        sorted_probs = sorted(
            [(team, prob) for team, prob in probs.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_probs
    
    def get_team_position_distribution(self, team_id):
        """Get position probability distribution for a team"""
        if team_id not in self.results["position_probability"]:
            return None
        
        return self.results["position_probability"][team_id]
    
    def get_top_n_likely_playoff_teams(self, n=4):
        """Get top N most likely playoff teams"""
        sorted_probs = self.get_qualification_probabilities()
        return sorted_probs[:n]
    
    def get_team_qualification_status(self, team_id):
        """Get qualification status for a team"""
        if team_id not in self.results["qualification_probability"]:
            return "Unknown"
        
        prob = self.results["qualification_probability"][team_id]
        
        if prob >= 0.99:
            return "Virtually Certain"
        elif prob >= 0.95:
            return "Very Likely"
        elif prob >= 0.75:
            return "Likely"
        elif prob >= 0.5:
            return "Toss-up"
        elif prob >= 0.25:
            return "Unlikely"
        elif prob >= 0.05:
            return "Very Unlikely"
        else:
            return "Virtually Eliminated"
    
    def find_current_playoff_cutoff(self):
        """Find the current playoff cutoff (points of 4th place team)"""
        # Sort standings by points, then NRR
        sorted_standings = sorted(
            self.standings,
            key=lambda x: (x["points"], x["nrr"]),
            reverse=True
        )
        
        if len(sorted_standings) >= 4:
            return sorted_standings[3]["points"]
        
        return None
    
    def calculate_expected_cutoff(self):
        """Calculate expected playoff cutoff based on simulations"""
        # Get current 4th place points
        sorted_standings = sorted(
            self.standings,
            key=lambda x: (x["points"], x["nrr"]),
            reverse=True
        )
        current_cutoff = sorted_standings[3]["points"] if len(sorted_standings) >= 4 else 0
        
        # Average remaining matches per team
        remaining_matches_per_team = 14 - sum(1 for team in self.standings if team["played"]) / len(self.standings)
        avg_points_per_team = remaining_matches_per_team * 2 * 0.5  # Each team wins 50% of remaining games
        
        # Use position probabilities to find likely 4th place teams
        fourth_place_probs = {}
        for team, positions in self.results["position_probability"].items():
            # Position 3 is 4th place (0-indexed)
            fourth_place_probs[team] = positions[3]
        
        # Get weighted average of points based on probability of finishing 4th
        total_prob = sum(fourth_place_probs.values())
        if total_prob == 0:
            # Fallback if calculations fail
            return max(14, current_cutoff + 4)
        
        weighted_points = 0
        for team, prob in fourth_place_probs.items():
            # Get current points
            team_standing = next((t for t in self.standings if t["team"] == team), None)
            if team_standing:
                # Weight by probability of finishing 4th
                current_points = team_standing["points"]
                
                # Estimate expected final points (add approximately half of remaining points)
                remaining_matches = 14 - team_standing["played"]
                estimated_additional_points = remaining_matches * 1  # Expecting to win half games
                
                weighted_points += (current_points + estimated_additional_points) * prob / total_prob
        
        return max(int(weighted_points), current_cutoff + 2)
    
    def generate_qualification_scenarios(self, team_id):
        """Generate qualification scenarios for a specific team"""
        # Get team standing
        team_standing = next((t for t in self.standings if t["team"] == team_id), None)
        if not team_standing:
            return None
        
        current_points = team_standing["points"]
        expected_cutoff = self.calculate_expected_cutoff()
        
        if expected_cutoff is None:
            expected_cutoff = 16  # Fallback to typical cutoff
        
        points_needed = max(0, expected_cutoff - current_points)
        wins_needed = (points_needed + 1) // 2  # Round up
        
        return {
            "team": team_id,
            "current_points": current_points,
            "expected_cutoff": expected_cutoff,
            "points_needed": points_needed,
            "wins_needed": wins_needed,
            "qualification_probability": self.results["qualification_probability"][team_id]
        }
    
    def generate_playoff_report(self):
        """Generate comprehensive playoff qualification report"""
        qualification_probs = self.get_qualification_probabilities()
        current_cutoff = self.find_current_playoff_cutoff()
        expected_cutoff = self.calculate_expected_cutoff()
        
        team_scenarios = {}
        for team_id in self.results["qualification_probability"]:
            team_scenarios[team_id] = self.generate_qualification_scenarios(team_id)
        
        return {
            "qualification_probabilities": qualification_probs,
            "current_cutoff": current_cutoff,
            "expected_cutoff": expected_cutoff,
            "team_scenarios": team_scenarios
        }