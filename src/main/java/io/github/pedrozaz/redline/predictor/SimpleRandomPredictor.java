package io.github.pedrozaz.redline.predictor;

import io.github.pedrozaz.redline.client.dto.Driver;
import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;
import org.springframework.stereotype.Component;

import java.util.*;

@Component
public class SimpleRandomPredictor implements RacePredictor {

    private static final List<Double> RACE_POINTS = List.of(
            25.0, 18.0, 15.0, 12.0, 10.0, 8.0, 6.0, 4.0, 2.0, 1.0
    );

    private static final List<Double> SPRINT_POINTS = List.of(
            8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0
    );

    @Override
    public Map<String, Double> predictRaceResults(List<DriverStanding> currentStandings, EventType eventType) {
        List<Double> pointsToAward = (eventType == EventType.SPRINT) ? SPRINT_POINTS : RACE_POINTS;

        List<DriverStanding> driverToShuffle = new ArrayList<>(currentStandings);
        Collections.shuffle(driverToShuffle);

        Map<String, Double> raceResults = new HashMap<>();

        for (int i = 0; i < pointsToAward.size(); i++) {
            if (i >= driverToShuffle.size()) {
                break;
            }
            DriverStanding winningDriver = driverToShuffle.get(i);
            double points = pointsToAward.get(i);
            raceResults.put(winningDriver.driver().driverId(), points);
        }
        return raceResults;
    }
}
