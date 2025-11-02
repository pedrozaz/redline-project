package io.github.pedrozaz.redline.client.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record Circuit(
        @JsonProperty("circuitId") String circuitId,
        @JsonProperty("circuitName") String circuitName
) {
}
