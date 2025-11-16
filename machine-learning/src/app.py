from flask import Flask, request, jsonify
import src.model.simulate_championship as simulation_runner
import os

app = Flask(__name__)

print("Model loaded. API is ready.")

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()

    if not data or 'currentStandings' not in data or 'remainingRaces' not in data:
        return jsonify({"error": "Missing 'currentStandings' or 'remainingRaces' in request"}), 400

    standings_json = data['currentStandings']
    races_json = data['remainingRaces']

    probabilities = simulation_runner.run_full_simulation(
        standings_json,
        races_json
    )

    return jsonify(probabilities)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)