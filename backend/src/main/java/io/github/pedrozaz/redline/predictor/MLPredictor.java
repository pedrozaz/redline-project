package io.github.pedrozaz.redline.predictor;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.pedrozaz.redline.client.DriverIdMapper;
import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.Race;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class MLPredictor {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final DriverIdMapper driverIdMapper;

    private static final String PYTHON_API_URL = "http://localhost:5000/simulate";

    public MLPredictor(RestTemplate restTemplate, ObjectMapper objectMapper, DriverIdMapper driverIdMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
        this.driverIdMapper = driverIdMapper;
    }

    public Map<String, Double> runFullSimulation(List<DriverStanding> standings, List<Race> races) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            List<Map<String, Object>> translatedStandings = standings.stream()
                    .map(this::translateStanding)
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());

            Map<String, Object> requestBody = Map.of(
                    "currentStandings", translatedStandings,
                    "remainingRaces", races
            );

            String jsonBody = objectMapper.writeValueAsString(requestBody);
            HttpEntity<String> request = new HttpEntity<>(jsonBody, headers);

            String jsonResponse = restTemplate.postForObject(PYTHON_API_URL, request, String.class);

            return objectMapper.readValue(jsonResponse, new TypeReference<>() {
            });

        } catch (Exception e) {
            System.err.println("Falha ao chamar a API de simulação Python: " + e.getMessage());
            return Map.of("error", -1.0);
        }
    }

    private Map<String, Object> translateStanding(DriverStanding standing) {

        String dbDriverId = driverIdMapper.getDbDriverId(standing.driver().driverId()).orElse(null);
        String dbConstructorId = null;

        if (standing.constructors() != null && !standing.constructors().isEmpty()) {
            String jolpicaConstructorId = standing.constructors().get(0).constructorId();
            dbConstructorId = driverIdMapper.getDbConstructorId(jolpicaConstructorId).orElse(null);
        }

        if (dbDriverId == null || dbConstructorId == null) {
            System.err.println("Pulando piloto: " + standing.driver().driverId() + " (ID não encontrado no mapper ou construtor nulo)");
            return null;
        }

        return Map.of(
                "driver", Map.of("driverId", dbDriverId),
                "constructor", Map.of("constructorId", dbConstructorId),
                "points", standing.points()
        );
    }
}