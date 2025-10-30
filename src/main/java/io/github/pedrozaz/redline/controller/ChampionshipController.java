package io.github.pedrozaz.redline.controller;

import io.github.pedrozaz.redline.service.ChampionshipSimulatorService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class ChampionshipController {

    private final ChampionshipSimulatorService simulatorService;

    public ChampionshipController(ChampionshipSimulatorService simulatorService) {
        this.simulatorService = simulatorService;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> getSimulationResults() {
        Map<String, Object> simulationResults = simulatorService.runChampionshipSim();
        return ResponseEntity.ok(simulationResults);
    }
}
