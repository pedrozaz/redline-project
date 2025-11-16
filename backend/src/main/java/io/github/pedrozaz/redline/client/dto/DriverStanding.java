package io.github.pedrozaz.redline.client.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record DriverStanding(
        @JsonProperty("points") double points,
        @JsonProperty("Driver") Driver driver,
        @JsonProperty("Constructors") List<Constructor> constructors
        ) {
}
