# simulator.py
import random
import copy
from collections import defaultdict

class MonteCarloSimulator:
    def __init__(self, standings, schedule, elo_calculator):
        self.standings = standings
        self.schedule = schedule
        self.elo_calculator = elo_calculator
        self.teams = self._extract_teams()
    
    def _extract_teams(self):
        """Extract list of teams from standings"""
        return [team["team"] for team in self.standings]
    
    def _clone_standings(self):
        """Create a deep copy of standings for simulation"""
        return copy.deepcopy(self.standings)
    
    def _update_standings(self, standings, winner_id, loser_id):
        """Update standings after a match"""
        for team in standings:
            if team["team"] == winner_id:
                team["played"] += 1
                team["wins"] += 1
                team["points"] += 2
                # Note: NRR updates are simplified
                team["nrr"] = round(team["nrr"] + random.uniform(0.05, 0.15), 3)
            elif team["team"] == loser_id:
                team["played"] += 1
                team["losses"] += 1
                # Note: NRR updates are simplified
                team["nrr"] = round(team["nrr"] - random.uniform(0.05, 0.15), 3)
        
        return standings
    
    def _get_playoff_teams(self, standings):
        """Get the top 4 teams from standings"""
        # Sort by points, then NRR
        sorted_teams = sorted(
            standings,
            key=lambda x: (x["points"], x["nrr"]),
            reverse=True
        )
        
        # Return top 4 team IDs
        return [team["team"] for team in sorted_teams[:4]]
    
    def simulate_match(self, match, use_elo=True):
        """Simulate a single match"""
        home_team = match["homeTeam"]
        away_team = match["awayTeam"]
        
        if use_elo:
            # Use ELO ratings to determine win probability
            home_win_prob = self.elo_calculator.calculate_win_probability(home_team, away_team)
        else:
            # Use simple 50/50 probability
            home_win_prob = 0.5
        
        # Simulate match outcome
        if random.random() < home_win_prob:
            return home_team  # Home team wins
        else:
            return away_team  # Away team wins
    
    def run_simulation(self, iterations=10000, use_elo=True):
        """Run Monte Carlo simulation"""
        # Track qualification count for each team
        qualification_count = {team: 0 for team in self.teams}
        
        # Track position counts for each team (0-indexed positions)
        position_counts = {team: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for team in self.teams}
        
        # Debug info
        total_matches = len(self.schedule)
        print(f"Total matches in schedule: {total_matches}")
        
        for i in range(iterations):
            # Clone current standings for this simulation
            sim_standings = self._clone_standings()
            
            # Simulate all remaining matches
            matches_simulated = 0
            for match in self.schedule:
                winner = self.simulate_match(match, use_elo)
                loser = match["awayTeam"] if winner == match["homeTeam"] else match["homeTeam"]
                
                # Update standings
                sim_standings = self._update_standings(sim_standings, winner, loser)
                matches_simulated += 1
            
            # Sort final standings
            sorted_standings = sorted(
                sim_standings,
                key=lambda x: (x["points"], x["nrr"]),
                reverse=True
            )
            
            # Record positions
            for pos, team in enumerate(sorted_standings):
                team_id = team["team"]
                position_counts[team_id][pos] += 1
                
                # Record playoff qualification (top 4)
                if pos < 4:
                    qualification_count[team_id] += 1
            
            # Print progress occasionally
            if i % 1000 == 0 and i > 0:
                print(f"Completed {i} simulations, {matches_simulated} matches per sim")
        
        # Calculate qualification probabilities
        qualification_probability = {}
        position_probability = {}
        
        for team in self.teams:
            qualification_probability[team] = qualification_count[team] / iterations
            position_probability[team] = [count / iterations for count in position_counts[team]]
        
        # Print stats about top teams
        sorted_qual = sorted(qualification_probability.items(), key=lambda x: x[1], reverse=True)
        print("\nTop team qualification probabilities:")
        for team, prob in sorted_qual[:5]:
            print(f"{team}: {prob*100:.1f}%")
        
        return {
            "qualification_probability": qualification_probability,
            "position_probability": position_probability
        }
    
    def calculate_path_to_playoffs(self, team_id, iterations=1000):
        """Calculate minimum wins needed for playoff qualification"""
        # Get current team standing
        team_standing = next((t for t in self.standings if t["team"] == team_id), None)
        if not team_standing:
            print(f"Team with ID '{team_id}' not found in standings")
            # Return empty dict with structure instead of None
            return {0: {"potential_points": 0, "qualification_probability": 0}}
        
        # Get remaining matches for this team
        remaining_matches = [
            match for match in self.schedule
            if match["homeTeam"] == team_id or match["awayTeam"] == team_id
        ]
        remaining_count = len(remaining_matches)
        current_points = team_standing["points"]
        
        results = {}
        
        # Try each possible win count
        for wins in range(remaining_count + 1):
            potential_points = current_points + (wins * 2)
            
            # Run simulations with fixed win count
            qualification_prob = self._simulate_with_fixed_wins(team_id, wins, remaining_matches, iterations)
            
            results[wins] = {
                "potential_points": potential_points,
                "qualification_probability": qualification_prob
            }
            
            # If we've reached our threshold, we can stop
            if qualification_prob >= 0.9:
                results["min_wins_needed"] = wins
                results["min_points_needed"] = potential_points
                break
        
        return results
    
    def _simulate_with_fixed_wins(self, team_id, wins, remaining_matches, iterations=1000):
        """Run simulations with a fixed number of wins for a team"""
        qualification_count = 0
        
        for _ in range(iterations):
            # Clone standings
            sim_standings = self._clone_standings()
            
            # Simulate with fixed number of wins for the target team
            remaining_matches_copy = remaining_matches.copy()
            random.shuffle(remaining_matches_copy)
            
            # First wins matches: team wins
            for i in range(wins):
                if i < len(remaining_matches_copy):
                    match = remaining_matches_copy[i]
                    winner = team_id
                    loser = match["awayTeam"] if winner == match["homeTeam"] else match["homeTeam"]
                    sim_standings = self._update_standings(sim_standings, winner, loser)
            
            # Remaining matches: team loses
            for i in range(wins, len(remaining_matches_copy)):
                match = remaining_matches_copy[i]
                loser = team_id
                winner = match["awayTeam"] if loser == match["homeTeam"] else match["homeTeam"]
                sim_standings = self._update_standings(sim_standings, winner, loser)
            
            # Simulate other matches
            other_matches = [m for m in self.schedule if m not in remaining_matches]
            for match in other_matches:
                winner = self.simulate_match(match)
                loser = match["awayTeam"] if winner == match["homeTeam"] else match["homeTeam"]
                sim_standings = self._update_standings(sim_standings, winner, loser)
            
            # Check if team qualified
            playoff_teams = self._get_playoff_teams(sim_standings)
            if team_id in playoff_teams:
                qualification_count += 1
        
        return qualification_count / iterations