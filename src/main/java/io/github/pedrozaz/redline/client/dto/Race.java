package io.github.pedrozaz.redline.client.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.LocalDate;

@JsonIgnoreProperties(ignoreUnknown = true)
public record Race(
        @JsonProperty("raceName") String raceName,
        @JsonProperty("date")LocalDate date,
        @JsonProperty("Sprint") Sprint sprint
        ) {
}
