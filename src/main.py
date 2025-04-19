# main.py
from data_loader import DataLoader
from elo_calculator import EloCalculator
from simulator import MonteCarloSimulator
from analyzer import PlayoffsAnalyzer
import json
import time

def run_playoffs_prediction(iterations=10000):
    """Run the full playoffs prediction pipeline"""
    start_time = time.time()
    
    # 1. Load data
    print("Loading data...")
    data_loader = DataLoader()
    data = data_loader.load_all_data()
    
    # 2. Calculate ELO ratings
    print("Calculating ELO ratings...")
    elo_calculator = EloCalculator(
        data["standings"],
        data["form_factor"],
        data["home_away_stats"]
    )
    ratings = elo_calculator.get_ratings()
    
    # Print team ratings
    print("\nTeam ELO Ratings:")
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    for team, rating in sorted_ratings:
        team_name = next((t["name"] for t in data["teams"] if t["id"] == team), team)
        print(f"{team_name}: {rating:.1f}")
    
    # 3. Run Monte Carlo simulation
    print(f"\nRunning {iterations} Monte Carlo simulations...")
    simulator = MonteCarloSimulator(
        data["standings"],
        data["schedule"],
        elo_calculator
    )
    simulation_results = simulator.run_simulation(iterations=iterations, use_elo=True)
    
    # 4. Analyze results
    print("\nAnalyzing results...")
    analyzer = PlayoffsAnalyzer(
        simulation_results,
        data["standings"],
        data["teams"]
    )
    
    # 5. Generate report
    print("\nGenerating playoff report...")
    playoff_report = analyzer.generate_playoff_report()
    
    # 6. Display qualification probabilities
    print("\nPlayoff Qualification Probabilities:")
    qual_probs = playoff_report["qualification_probabilities"]
    for team, prob in qual_probs:
        team_name = next((t["name"] for t in data["teams"] if t["id"] == team), team)
        status = analyzer.get_team_qualification_status(team)
        print(f"{team_name}: {prob*100:.1f}% ({status})")
    
    # 7. Display expected cutoff
    expected_cutoff = playoff_report["expected_cutoff"]
    print(f"\nExpected playoff cutoff: {expected_cutoff} points")
    
    # 8. Display scenarios for each team
    print("\nTeam Qualification Scenarios:")
    for team_id, scenario in playoff_report["team_scenarios"].items():
        team_name = next((t["name"] for t in data["teams"] if t["id"] == team_id), team_id)
        print(f"\n{team_name}:")
        print(f"  Current points: {scenario['current_points']}")
        print(f"  Points needed: {scenario['points_needed']} (approx. {scenario['wins_needed']} wins)")
        print(f"  Qualification probability: {scenario['qualification_probability']*100:.1f}%")
    
    # 9. Save results to file
    with open("playoff_predictions.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "qualification_probabilities": {team: prob for team, prob in qual_probs},
            "expected_cutoff": expected_cutoff,
            "team_scenarios": playoff_report["team_scenarios"]
        }, f, indent=2)
    
    # Print execution time
    execution_time = time.time() - start_time
    print(f"\nExecution completed in {execution_time:.2f} seconds")
    
    return {
        "simulation_results": simulation_results,
        "playoff_report": playoff_report
    }

def analyze_specific_team(team_id, iterations=10000):
    """Run detailed analysis for a specific team"""
    # 1. Load data
    data_loader = DataLoader()
    data = data_loader.load_all_data()
    
    # Get team details
    team = None
    for t in data["teams"]:
        if t["id"] == team_id:
            team = t
            break
    
    if not team:
        print(f"Team with ID '{team_id}' not found")
        return None
    
    print(f"Detailed analysis for {team['name']}:")
    
    # 2. Setup ELO calculator and simulator
    elo_calculator = EloCalculator(data["standings"], data["form_factor"], data["home_away_stats"])
    simulator = MonteCarloSimulator(data["standings"], data["schedule"], elo_calculator)
    
    # 3. Calculate path to playoffs
    print("\nCalculating path to playoffs...")
    path_results = simulator.calculate_path_to_playoffs(team_id)
    
    # Check if path_results is None or empty
    if not path_results:
        print("Error: Could not calculate playoff path. Team may not exist in standings.")
        return None
    
    # Print results
    print("\nPlayoff path scenarios:")
    for wins, result in path_results.items():
        if isinstance(wins, str):  # Skip metadata keys
            continue
        print(f"With {wins} more wins ({result['potential_points']} total points): {result['qualification_probability']*100:.1f}% chance")
    
    if "min_wins_needed" in path_results:
        print(f"\nMinimum wins needed for 90% chance: {path_results['min_wins_needed']}")
    
    # 4. Run full simulation to get position probabilities
    print("\nRunning position probability simulation...")
    sim_results = simulator.run_simulation(iterations=iterations)
    
    # 5. Display position probabilities
    if team_id in sim_results["position_probability"]:
        position_probs = sim_results["position_probability"][team_id]
        print("\nPosition probability distribution:")
        for i, prob in enumerate(position_probs):
            print(f"Position {i+1}: {prob*100:.1f}%")
    else:
        print(f"No position probability data found for {team['name']}")
    
    return {
        "team": team,
        "path_results": path_results,
        "position_probabilities": sim_results["position_probability"].get(team_id, [])
    }

if __name__ == "__main__":
    # Run full prediction
    results = run_playoffs_prediction(iterations=10000)
    
    # Optional: Run detailed analysis for a specific team
    team_analysis = analyze_specific_team("LSG", iterations=10000)