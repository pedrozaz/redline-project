package io.github.pedrozaz.redline.client.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record Driver(
        @JsonProperty("driverId") String driverId,
        @JsonProperty("givenName") String givenName,
        @JsonProperty("familyName") String familyName
) {
}
