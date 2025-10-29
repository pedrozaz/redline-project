package io.github.pedrozaz.redline.client.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record StandingsTable(
        @JsonProperty("StandingsLists") List<StandingsList> standingsLists
) {
}
