import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/apiClient';
import type {SimulationResponse} from '../types';

const SIMULATION_QUERY_KEY = ['simulation'];

const fetchSimulation = async (): Promise<SimulationResponse> => {
    const { data } = await apiClient.get<SimulationResponse>('/simulate');
    return data;
}

export const useSimulationQuery = () => {
    return useQuery({
        queryKey: SIMULATION_QUERY_KEY,
        queryFn: fetchSimulation,
        enabled: false,
        retry: 0,
    });
};