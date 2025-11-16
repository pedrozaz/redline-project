package io.github.pedrozaz.redline.service;

import io.github.pedrozaz.redline.client.DriverIdMapper;
import io.github.pedrozaz.redline.client.F1ClientService;
import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;
import io.github.pedrozaz.redline.predictor.MLPredictor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ChampionshipSimulatorService {

    private final F1ClientService f1ClientService;
    private final MLPredictor simulationClient;
    private final DriverIdMapper driverIdMapper;

    public ChampionshipSimulatorService(F1ClientService f1ClientService,
                                        MLPredictor simulationClient,
                                        DriverIdMapper driverIdMapper) {
        this.f1ClientService = f1ClientService;
        this.simulationClient = simulationClient;
        this.driverIdMapper = driverIdMapper;
    }

    public Map<String, Object> runChampionshipSim() {
        List<DriverStanding> currentStandings = f1ClientService.getCurrentStandings();
        List<Race> remainingRaces = f1ClientService.getRemainingRaces();

        if (currentStandings.isEmpty() || remainingRaces.isEmpty()) {
            return Map.of("error", true,
                    "message", "Missing data or season ended.");
        }

        Map<String, Double> dbIdProbabilities = simulationClient.runFullSimulation(currentStandings, remainingRaces);

        if (dbIdProbabilities.containsKey("error")) {
            return Map.of("error", true,
                    "message", "Python simulation service failed.");
        }

        Map<String, ?> finalProbabilities = formatProbabilities(dbIdProbabilities, currentStandings);

        return Map.of(
                "error", false,
                "probabilities", finalProbabilities,
                "simulationsRun", 10000,
                "remainingRaces", remainingRaces.size()
        );
    }

    private Map<String, Double> formatProbabilities(Map<String, Double> dbIdProbs, List<DriverStanding> standings) {

        Map<String, String> jolpicaIdToNameMap = standings.stream()
                .collect(Collectors.toMap(
                        standing -> standing.driver().driverId(),
                        standing -> standing.driver().givenName() + " " + standing.driver().familyName(),
                        (existing, replacement) -> existing
                ));

        return dbIdProbs.entrySet().stream()
                .collect(Collectors.toMap(
                        entry -> {
                            String jolpicaId = driverIdMapper.getJolpicaDriverId(entry.getKey());
                            return jolpicaIdToNameMap.getOrDefault(jolpicaId, jolpicaId);
                        },
                        Map.Entry::getValue
                ));
    }
}
