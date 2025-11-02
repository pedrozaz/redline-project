package io.github.pedrozaz.redline.predictor;


import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

record MLRaceRequest(String circuit_name, int year) {}

@Service @Primary
public class MLPredictor implements RacePredictor {

    private static final Logger logger = LoggerFactory.getLogger(MLPredictor.class);

    private final WebClient mlApiWebClient;

    private static final Map<String, String> CIRCUIT_ID_TO_NAME_MAP = new HashMap<>();
    static {
        CIRCUIT_ID_TO_NAME_MAP.put("bahrain", "Sakhir");
        CIRCUIT_ID_TO_NAME_MAP.put("jeddah", "Jeddah");
        CIRCUIT_ID_TO_NAME_MAP.put("albert_park", "Melbourne");
        CIRCUIT_ID_TO_NAME_MAP.put("suzuka", "Suzuka");
        CIRCUIT_ID_TO_NAME_MAP.put("shanghai", "Shanghai");
        CIRCUIT_ID_TO_NAME_MAP.put("miami", "Miami");
        CIRCUIT_ID_TO_NAME_MAP.put("imola", "Imola");
        CIRCUIT_ID_TO_NAME_MAP.put("monaco", "Monte Carlo");
        CIRCUIT_ID_TO_NAME_MAP.put("villeneuve", "Montreal");
        CIRCUIT_ID_TO_NAME_MAP.put("catalunya", "Catalunya");
        CIRCUIT_ID_TO_NAME_MAP.put("red_bull_ring", "Spielberg");
        CIRCUIT_ID_TO_NAME_MAP.put("silverstone", "Silverstone");
        CIRCUIT_ID_TO_NAME_MAP.put("hungaroring", "Hungaroring");
        CIRCUIT_ID_TO_NAME_MAP.put("spa", "Spa-Francorchamps");
        CIRCUIT_ID_TO_NAME_MAP.put("zandvoort", "Zandvoort");
        CIRCUIT_ID_TO_NAME_MAP.put("monza", "Monza");
        CIRCUIT_ID_TO_NAME_MAP.put("baku", "Baku");
        CIRCUIT_ID_TO_NAME_MAP.put("marina_bay", "Singapore");
        CIRCUIT_ID_TO_NAME_MAP.put("americas", "Austin");
        CIRCUIT_ID_TO_NAME_MAP.put("rodriguez", "Mexico City");
        CIRCUIT_ID_TO_NAME_MAP.put("interlagos", "Interlagos");
        CIRCUIT_ID_TO_NAME_MAP.put("vegas", "Las Vegas");
        CIRCUIT_ID_TO_NAME_MAP.put("losail", "Lusail");
        CIRCUIT_ID_TO_NAME_MAP.put("yas_marina", "Yas Marina Circuit");
    }

    public MLPredictor(WebClient mlApiWebClient) {
        this.mlApiWebClient = mlApiWebClient;
    }

    @Override
    public Map<String, Double> predictRaceResults(List<DriverStanding> currentStandings, Race race) {
        String jolpicaCircuitId = race.circuit().circuitId();
        String openF1CircuitName = CIRCUIT_ID_TO_NAME_MAP.get(jolpicaCircuitId);
        int year = race.date().getYear();

        if (openF1CircuitName == null) {
            logger.error("Invalid circuit ID: {}", jolpicaCircuitId);
            return new HashMap<>();
        }

        MLRaceRequest requestBody = new MLRaceRequest(openF1CircuitName, year);
        logger.info("Calling ML with {}", requestBody);

        try {
            Map<String, Double> prediction = mlApiWebClient.post()
                    .uri("simulate_race_results")
                    .body(Mono.just(requestBody), MLRaceRequest.class)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (prediction == null || prediction.isEmpty()) {
                logger.warn("Python API returned empty results for {}", requestBody);
                return new HashMap<>();
            }

            logger.info("Success. Returned {} results", prediction.size());
            return prediction;
        } catch (Exception e) {
            logger.error("Error while calling ML with {}", requestBody, e);
            return new HashMap<>();
        }
    }
}
