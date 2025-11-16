package io.github.pedrozaz.redline.client;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Component
public class DriverIdMapper {
    private static final Map<String, String> JOLPICA_TO_DB_ID_MAP = Map.ofEntries(
            Map.entry("max_verstappen", "1"),
            Map.entry("hamilton", "44"),
            Map.entry("leclerc", "16"),
            Map.entry("norris", "4"),
            Map.entry("sainz", "55"),
            Map.entry("piastri", "81"),
            Map.entry("russell", "63"),
            Map.entry("perez", "11"),
            Map.entry("alonso", "14"),
            Map.entry("stroll", "18"),
            Map.entry("tsunoda", "22"),
            Map.entry("ricciardo", "3"),
            Map.entry("hulkenberg", "27"),
            Map.entry("kevin_magnussen", "20"),
            Map.entry("albon", "23"),
            Map.entry("sargeant", "2"),
            Map.entry("gasly", "10"),
            Map.entry("ocon", "31"),
            Map.entry("bottas", "77"),
            Map.entry("zhou", "24"),
            Map.entry("bearman", "38")
    );

    private static final Map<String, String> CONSTRUCTOR_JOLPICA_TO_DB_MAP = Map.of(
            "red_bull", "Red Bull",
            "mercedes", "Mercedes",
            "ferrari", "Ferrari",
            "mclaren", "McLaren",
            "aston_martin", "Aston Martin",
            "alpine", "Alpine",
            "rb", "RB",
            "sauber", "Sauber",
            "haas", "Haas F1 Team",
            "williams", "Williams"
    );

    private static final Map<String, String> DB_ID_TO_JOLPICA_MAP =
            JOLPICA_TO_DB_ID_MAP.entrySet().stream()
                    .collect(Collectors.toMap(Map.Entry::getValue, Map.Entry::getKey));

    public Optional<String> getDbDriverId(String jolpicaDriverId) {
        return Optional.ofNullable(JOLPICA_TO_DB_ID_MAP.get(jolpicaDriverId));
    }

    public Optional<String> getDbConstructorId(String jolpicaConstructorId) {
        return Optional.ofNullable(CONSTRUCTOR_JOLPICA_TO_DB_MAP.get(jolpicaConstructorId));
    }

    public String getJolpicaDriverId(String dbDriverId) {
        return DB_ID_TO_JOLPICA_MAP.getOrDefault(dbDriverId, dbDriverId);
    }
}
