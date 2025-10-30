package io.github.pedrozaz.redline.predictor;

import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;

import java.util.List;
import java.util.Map;

public interface RacePredictor {
    Map<String, Double> predictRaceResults(List<DriverStanding> currentStandings, EventType eventType);
}
