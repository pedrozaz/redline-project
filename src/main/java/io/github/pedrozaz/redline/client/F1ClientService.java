package io.github.pedrozaz.redline.client;

import io.github.pedrozaz.redline.client.dto.DriverStanding;
import io.github.pedrozaz.redline.client.dto.ErgastResponse;
import io.github.pedrozaz.redline.client.dto.Race;
import io.github.pedrozaz.redline.client.dto.ScheduleResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
public class F1ClientService {

    private static final String API_BASE_URL = "https://api.jolpi.ca/ergast/f1/";
    private final RestTemplate restTemplate;

    public F1ClientService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public List<DriverStanding> getCurrentStandings() {
        String url = API_BASE_URL + "current/currentStandings.json";

        try {
            ErgastResponse response = restTemplate.getForObject(url, ErgastResponse.class);

            if (response != null &
            response.mrData() != null &
            response.mrData().standingsTable() != null &
            response.mrData().standingsTable().standingsLists() != null &
            !response.mrData().standingsTable().standingsLists().isEmpty()) {

                return response.mrData().standingsTable().standingsLists().get(0).driverStandings();
            }
        } catch (Exception e) {
            log.error("Error while searching API season standings: {}", e.getMessage());
        }
        return Collections.emptyList();
    }

    public List<Race> getSeasonSchedule() {
        String url = API_BASE_URL + "current.json";

        try {
            ScheduleResponse response = restTemplate.getForObject(url, ScheduleResponse.class);

            if (response != null &
            response.mrData() != null &
            response.mrData().raceTable() != null &
            response.mrData().raceTable().races() != null) {

                return response.mrData().raceTable().races();
            }
        } catch (Exception e) {
            log.error("Error while searching API season schedule: {}", e.getMessage());
        }
        return  Collections.emptyList();
    }

    public List<Race> getRemainingRaces() {
        List<Race> allRaces = getSeasonSchedule();
        LocalDate today = LocalDate.now();

        return allRaces.stream()
                .filter(race -> race.date().isAfter(today))
                .collect(Collectors.toList());
    }
}
