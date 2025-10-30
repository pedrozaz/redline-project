export interface DriverProbability {
    [driverName: string]: number;
}

export interface SimulationSuccessResponse {
    error: false;
    probabilities: DriverProbability;
    simulationsRun: number;
    remainingRaces: number;
}

export interface SimulationErrorResponse {
    error: true;
    message: string;
}

export type SimulationResponse =
    | SimulationSuccessResponse
    | SimulationErrorResponse;