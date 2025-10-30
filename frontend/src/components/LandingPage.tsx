import {
    Box,
    Button,
    Heading,
    Text,
    Spinner,
    Code,
} from '@chakra-ui/react';

import { useSimulationQuery } from '../hooks/useSimulationQuery';
import type {SimulationErrorResponse, SimulationSuccessResponse} from '../types';

function LandingPage() {
    const { data, isLoading, isError, refetch } = useSimulationQuery();
    const handleSimulateClick = () => {
        refetch();
    }
    const renderResults = () => {
        if (isLoading) {
            return <Spinner size={"xl"} color={"red.500"} />;
        }

        if (isError) {
            return (
                <Text color={"red.400"}>
                    Error connecting to the API. Please try again later.
                </Text>
            );
        }
        if (data) {
            if (data.error) {
                return (
                    <Text color={"yellow.400"}>
                        API Error: {(data as SimulationErrorResponse).message}
                    </Text>
                );
            }

            const successData = data as SimulationSuccessResponse;

            return (
                <Box textAlign={"left"} mt={4}>
                    <Heading size={"md"}>
                        Simulation Results ({successData.simulationsRun} races simulated):
                    </Heading>
                    <Code
                        as={"pre"}
                        p={4}
                        rounded={"md"}
                        bg={"gray.700"}
                        mt={2}
                        overflowX="auto"
                        >
                        {JSON.stringify(successData.probabilities, null, 2)}
                    </Code>
                </Box>
            );
        }
        return <Text>Click the button to start the simulation.</Text>
    }

    return (
        <Box
            textAlign={"center"}
            padding={8}
            minHeight={"100vh"}
            >
            <Heading mb={6}>Redline: F1 Championship Simulator</Heading>

            <Button
                colorScheme={"red"}
                onClick={handleSimulateClick}
                isLoading={isLoading}
                >
                Simulate Championship
            </Button>
            <Box mt={8}>{renderResults()}</Box>
        </Box>
    );
}

export default LandingPage;