import {
    Box,
    Button,
    Heading,
    Text,
    Spinner,
    Code,
} from '@chakra-ui/react';

import { useSimulationQuery } from './hooks/useSimulationQuery';
import type {SimulationErrorResponse, SimulationSuccessResponse} from './types';

function App() {

    const { data, isLoading, isError, refetch } = useSimulationQuery();

    const handleSimulateClick = () => {
        refetch();
    };

    const renderResults = () => {
        if (isLoading) {
            return <Spinner size="xl" color="red.500" />;
        }

        if (isError) {
            return (
                <Text color="red.400">
                    Error while fetching simulation results.
                </Text>
            );
        }

        if (data) {
            if (data.error) {
                return (
                    <Text color="yellow.400">
                        API Error: {(data as SimulationErrorResponse).message}
                    </Text>
                );
            }

            const successData = data as SimulationSuccessResponse;

            return (
                <Box textAlign="left" mt={4}>
                    <Heading size="md">
                        Simulation results: ({successData.simulationsRun} corridas):
                    </Heading>
                    <Code as="pre" p={4} rounded="md" bg="gray.700" mt={2} overflowX="auto">
                        {JSON.stringify(successData.probabilities, null, 2)}
                    </Code>
                </Box>
            );
        }

        return <Text>Click at the button to start simulation.</Text>;
    };

    return (
        <Box
            textAlign="center"
            padding={8}
            bg="gray.800"
            color="white"
            minHeight="100vh"
        >
            <Heading mb={6}>Redline: F1 Championship Simulator</Heading>

            <Button
                colorScheme="red"
                onClick={handleSimulateClick}
                loading={isLoading}
            >
                Simulate Championship
            </Button>

            <Box mt={8}>{renderResults()}</Box>
        </Box>
    );
}

export default App;