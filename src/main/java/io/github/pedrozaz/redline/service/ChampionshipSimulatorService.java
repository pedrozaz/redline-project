package io.github.pedrozaz.redline.service;

import io.github.pedrozaz.redline.client.F1ClientService;
import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;
import io.github.pedrozaz.redline.predictor.EventType;
import io.github.pedrozaz.redline.predictor.RacePredictor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ChampionshipSimulatorService {

    private static final int SIMULATION_COUNT = 10_000;

    private final F1ClientService f1ClientService;
    private final RacePredictor racePredictor;

    public ChampionshipSimulatorService(F1ClientService f1ClientService, RacePredictor racePredictor) {
        this.f1ClientService = f1ClientService;
        this.racePredictor = racePredictor;
    }

    public Map<String, Object> runChampionshipSim() {
        List<DriverStanding> currentStandings = f1ClientService.getCurrentStandings();
        List<Race> remainingRaces = f1ClientService.getRemainingRaces();

        if (currentStandings.isEmpty() || remainingRaces.isEmpty()) {
            return Map.of("error", true,
                    "message", "Missing data or season ended.");
        }

        Map<String, Integer> championshipWinsCount = initWinCounter(currentStandings);

        for (int i = 0; i < SIMULATION_COUNT; i++) {
            String seasonWinnerDriverId = simulateOneSeason(currentStandings, remainingRaces);
            championshipWinsCount.merge(seasonWinnerDriverId, 1, Integer::sum);
        }

        Map<String, ?> probabilities = calculateProbabilities(championshipWinsCount, currentStandings);

        return Map.of(
                "error", false,
                "probabilities", probabilities,
                "simulationsRun", SIMULATION_COUNT,
                "remainingRaces", remainingRaces.size()
        );
    }

    private String simulateOneSeason(List<DriverStanding> initialStandings, List<Race> remainingRaces) {
        Map<String, Double> simulatedStandings = initSimulatedStandings(initialStandings);

        for (Race race : remainingRaces) {
            Map<String, Double> raceResults = racePredictor.predictRaceResults(initialStandings, EventType.RACE);

            raceResults.forEach((driverId, points) ->
                    simulatedStandings.merge(driverId, points, Double::sum));

            if (race.sprint() != null) {
                Map<String, Double> sprintResults = racePredictor.predictRaceResults(initialStandings, EventType.SPRINT);

                sprintResults.forEach((driverId, points) ->
                        simulatedStandings.merge(driverId, points, Double::sum));
            }
        }
        return findSeasonWinner(simulatedStandings);
    }

    private Map<String, Double> initSimulatedStandings(List<DriverStanding> standings) {
        return standings.stream()
                .collect(Collectors.toMap(
                        standing -> standing.driver().driverId(),
                        DriverStanding::points
                ));
    }

    private Map<String, Integer> initWinCounter(List<DriverStanding> standings) {
        return standings.stream()
                .collect(Collectors.toMap(
                        standing -> standing.driver().driverId(),
                        standing -> 0
                ));
    }

    private String findSeasonWinner(Map<String, Double> finalStandings) {
        return finalStandings.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse("no_winner");
    }

    private Map<String, Object> calculateProbabilities(Map<String, Integer> winCounter, List<DriverStanding> standings) {
        Map<String, String> driverIdToNameMap = standings.stream()
                .collect(Collectors.toMap(
                        standing -> standing.driver().driverId(),
                        standing -> standing.driver().givenName() + " " + standing.driver().familyName()
                ));
        return winCounter.entrySet().stream()
                .collect(Collectors.toMap(
                        entry -> driverIdToNameMap.get(entry.getKey()),
                        entry -> (double) entry.getValue() / SIMULATION_COUNT * 100.0
                ));
    }
}
