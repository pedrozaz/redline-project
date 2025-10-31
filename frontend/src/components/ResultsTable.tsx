import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import type {DriverProbability} from '../types';

interface ResultsTableProps {
    probabilities: DriverProbability;
}

function ResultsTable({ probabilities }: ResultsTableProps) {
    const sortedProbabilities = Object.entries(probabilities)
        .sort(([, probA], [, probB]) => probB - probA)
        .filter(([, prob]) => prob > 0);

    return (
        <Box
            maxW={"700px"}
            mx="auto"
            border={"1px solid"}
            borderColor={"gray.200"}
            borderRadius={"md"}
            overflowX="hidden"
            >
            <Heading
                size={"md"}
                p={4}
                bg={"gray.100"}
                borderBottom={"1px solid"}
                borderColor={"gray.200"}
                >
                Championship Odds
            </Heading>

            <Box>
                {sortedProbabilities.map(([driverName, probability], index) => (
                    <Flex
                    key={driverName}
                    justify="space-between"
                    align={"center"}
                    p={4}
                    bg={index % 2 === 0 ? 'brand.white' : 'gray.50'}
                    borderBottom={"1px solid"}
                    borderColor={"gray.200"}
                    >
                        <Flex align={"center"} gap={4}>
                            <Text fontWeight={"bold"} color={"gray.500"} minW={"30px"}>
                                {index + 1}
                            </Text>
                            <Text fontWeight={"medium"}>{driverName}</Text>
                        </Flex>
                        <Text fontWeight={"bold"} color={"red.500"}>
                            {probability.toFixed(2)}%
                        </Text>
                    </Flex>
                ))}
            </Box>
        </Box>
    )
}

export default ResultsTable;