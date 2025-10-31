import {
    Box,
    Button,
    Heading,
    Text,
    Spinner,
    Image,
} from '@chakra-ui/react';
import { useSimulationQuery } from '../hooks/useSimulationQuery';
import type {
    SimulationErrorResponse,
    SimulationSuccessResponse,
    DriverProbability,
} from '../types';
import { driverAssetMap, placeholderAssets } from '../assets/driverAssets';
import ResultsTable from './ResultsTable';

const findWinner = (probabilities: DriverProbability): string => {
    const winnerEntry = Object.entries(probabilities).reduce(
        (max, current) => (current[1] > max[1] ? current : max),
        ['', 0]
    );
    return winnerEntry[0];
};

function LandingPage() {
    const { data, isLoading, isError, refetch } = useSimulationQuery();

    const handleSimulateClick = () => {
        refetch();
    };

    const renderResults = () => {
        if (isLoading) {
            return (
                <Box
                    position="absolute"
                    top="50%"
                    left="50%"
                    transform="translate(-50%, -50%)"
                    zIndex={1}
                >
                    <Spinner size={'xl'} color={'red.500'} />
                </Box>
            );
        }

        if (isError) {
            return (
                <Box
                    position="absolute"
                    top="50%"
                    left="50%"
                    transform="translate(-50%, -50%)"
                    zIndex={1}
                >
                    <Text color={'red.400'}>
                        Error connecting to the API. Please try again later.
                    </Text>
                </Box>
            );
        }

        if (data) {
            if (data.error) {
                return (
                    <Box
                        position="absolute"
                        top="50%"
                        left="50%"
                        transform="translate(-50%, -50%)"
                        zIndex={1}
                    >
                        <Text color={'yellow.600'}>
                            API Error: {(data as SimulationErrorResponse).message}
                        </Text>
                    </Box>
                );
            }

            const successData = data as SimulationSuccessResponse;
            const winnerName = findWinner(successData.probabilities);

            const assets = driverAssetMap[winnerName] || placeholderAssets;
            const mainImageUrl = `/assets/drivers/${assets.main}`;

            return (
                <Box>
                    <Box
                        position="relative"
                        width="100%"
                        height={{ base: '75vh', md: '90vh' }}
                        overflow="hidden"
                    >
                        <Heading
                            position="absolute"
                            top="50%"
                            left="50%"
                            transform="translate(-50%, -50%)"
                            zIndex={1}
                            fontSize={{ base: '6rem', md: '12rem', lg: '14rem' }}
                            fontWeight="bold"
                            textTransform="uppercase"
                            opacity={0.25}
                            color="gray.700"
                            whiteSpace="nowrap"
                            textShadow="0 10px 30px rgba(0,0,0,0.5)"
                        >
                            {winnerName}
                        </Heading>

                        <Image
                            src={mainImageUrl}
                            alt={winnerName}
                            position="absolute"
                            bottom="0"
                            left="50%"
                            transform="translateX(-50%)"
                            height={{ base: '60vh', md: '75vh' }}
                            width="auto"
                            objectFit="contain"
                            objectPosition="bottom center"
                            zIndex={2}
                        />
                    </Box>

                    <Box py={20}>
                        <ResultsTable probabilities={successData.probabilities} />
                    </Box>
                </Box>
            );
        }

        return (
            <Box
                position="absolute"
                top="50%"
                left="50%"
                transform="translate(-50%, -50%)"
                zIndex={1}
            >
                <Text>Click the button to start the simulation.</Text>
            </Box>
        );
    };

    return (
        <Box
            textAlign={'center'}
            padding={8}
            minHeight={'100vh'}
            position="relative"
        >
            <Box zIndex={10}>
                <Heading mb={6}>Redline: F1 Championship Simulator</Heading>
                <Button
                    colorScheme={'red'}
                    onClick={handleSimulateClick}
                    isLoading={isLoading}
                >
                    Simulate Championship
                </Button>
            </Box>

            <Box>{renderResults()}</Box>
        </Box>
    );
}

export default LandingPage;