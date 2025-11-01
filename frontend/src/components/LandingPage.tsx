import { useEffect, useState } from 'react';
import {
    Box,
    Button,
    Heading,
    Text,
    Spinner,
    Image,
    Container,
    VStack,
} from '@chakra-ui/react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useQueryClient } from '@tanstack/react-query';
import { useSimulationQuery } from '../hooks/useSimulationQuery';
import type {
    SimulationErrorResponse,
    SimulationSuccessResponse,
    DriverProbability,
} from '../types';
import { driverAssetMap, placeholderAssets } from '../assets/driverAssets';
import ResultsTable from './ResultsTable';

const MotionBox = motion(Box);
const MotionHeading = motion(Heading);
const MotionText = motion(Text);
const MotionImage = motion(Image);

const findWinner = (probabilities: DriverProbability): string => {
    const winnerEntry = Object.entries(probabilities).reduce(
        (max, current) => (current[1] > max[1] ? current : max),
        ['', 0]
    );
    return winnerEntry[0];
};

const SubtleParticles = () => {
    const particles = Array.from({ length: 20 }, (_, i) => i);

    return (
        <Box position="absolute" top="0" left="0" right="0" bottom="0" overflow="hidden" pointerEvents="none">
            {particles.map((i) => (
                <MotionBox
                    key={i}
                    position="absolute"
                    width="3px"
                    height="3px"
                    borderRadius="50%"
                    bg="gray.300"
                    opacity={0.4}
                    left={`${Math.random() * 100}%`}
                    top={`${Math.random() * 100}%`}
                    animate={{
                        y: [0, -20, 0],
                        opacity: [0.2, 0.5, 0.2],
                    }}
                    transition={{
                        duration: Math.random() * 4 + 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: Math.random() * 2,
                    }}
                />
            ))}
        </Box>
    );
};

function LandingPage() {
    const { data, isLoading, isRefetching, isError, refetch } = useSimulationQuery(); //
    const queryClient = useQueryClient();
    const { scrollYProgress } = useScroll();
    const [hasScrolled, setHasScrolled] = useState(false);

    useEffect(() => {
        if (!isLoading && data && !data.error) {
            setHasScrolled(false);
        }
    }, [isLoading, data]);

    useEffect(() => {
        const unsubscribe = scrollYProgress.on('change', (latest) => {
            if (latest > 0.01 && !hasScrolled) {
                setHasScrolled(true);
            }
        });

        return () => unsubscribe();
    }, [scrollYProgress, hasScrolled]);

    const textOpacity = useTransform(
        scrollYProgress,
        [0, 0.3, 0.5],
        hasScrolled ? [0.12, 0.08, 1] : [0.12, 0.12, 0.12]
    );

    const textY = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [0, 200] : [0, 0]
    );

    const textSize = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [1, 0.35] : [1, 1]
    );

    const seasonWinnerOpacity = useTransform(
        scrollYProgress,
        [0, 0.5, 0.7],
        hasScrolled ? [0, 0, 1] : [0, 0, 0]
    );

    const seasonWinnerY = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [0, 250] : [0, 0]
    );

    const imageY = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [0, -350] : [0, 0]
    );

    const imageScale = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [1, 0.35] : [1, 1]
    );

    const frameScale = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [1, 0.35] : [1, 1]
    );

    const frameY = useTransform(
        scrollYProgress,
        [0, 0.5],
        hasScrolled ? [0, -350] : [0, 0]
    );

    const handleSimulateClick = () => {
        setHasScrolled(false);
        refetch();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleLogoClick = () => {
        queryClient.resetQueries({ queryKey: ['simulation'] });
        setHasScrolled(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const renderContent = () => {
        if (isLoading || isRefetching) { //
            return (
                <MotionBox
                    position="fixed"
                    top="0"
                    left="0"
                    width="100vw"
                    height="100vh"
                    bg="white"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    zIndex={100}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <VStack spacing={6}>
                        <Spinner size="xl" color="gray.800" thickness="3px" speed="0.8s" />
                        <Text color="gray.600" fontSize="sm" fontWeight="500" letterSpacing="widest">
                            SIMULATING
                        </Text>
                    </VStack>
                </MotionBox>
            );
        }

        if (isError) {
            return (
                <Container maxW="container.md" py={20}>
                    <MotionBox
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        bg="red.50"
                        p={8}
                        borderRadius="xl"
                        border="1px solid"
                        borderColor="red.200"
                    >
                        <Text color="red.800" fontSize="lg" fontWeight="600">
                            Connection Error
                        </Text>
                        <Text color="red.600" mt={2}>
                            Unable to connect to the API. Please try again later.
                        </Text>
                    </MotionBox>
                </Container>
            );
        }

        if (data) {
            if (data.error) {
                return (
                    <Container maxW="container.md" py={20}>
                        <MotionBox
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            bg="yellow.50"
                            p={8}
                            borderRadius="xl"
                            border="1px solid"
                            borderColor="yellow.200"
                        >
                            <Text color="yellow.800" fontSize="lg" fontWeight="600">
                                API Error
                            </Text>
                            <Text color="yellow.700" mt={2}>
                                {(data as SimulationErrorResponse).message}
                            </Text>
                        </MotionBox>
                    </Container>
                );
            }

            const successData = data as SimulationSuccessResponse;
            const winnerName = findWinner(successData.probabilities);
            const assets = driverAssetMap[winnerName] || placeholderAssets;
            const mainImageUrl = `/assets/drivers/${assets.main}`;

            return (
                <MotionBox
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                >
                    {/* Hero Section */}
                    <Box
                        position="relative"
                        width="100%"
                        height={{ base: '85vh', md: '92vh' }}
                        overflow="hidden"
                        bg="linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%)"
                    >
                        {/* Subtle animated grid */}
                        <Box
                            position="absolute"
                            top="0"
                            left="0"
                            right="0"
                            bottom="0"
                            opacity={0.03}
                            backgroundImage="linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)"
                            backgroundSize="50px 50px"
                        />

                        <Box
                            position="absolute"
                            top="0"
                            left="0"
                            right="0"
                            bottom="0"
                            bg="radial-gradient(ellipse at center, transparent 70%, rgba(25, 25, 25, 0.1) 100%)"
                            pointerEvents="none"
                        />


                        {/* Subtle Particles */}
                        <SubtleParticles />

                        {/* Soft gradient orb */}
                        <MotionBox
                            position="absolute"
                            top="20%"
                            right="10%"
                            width="400px"
                            height="400px"
                            borderRadius="50%"
                            bg="radial-gradient(circle, rgba(229, 229, 229, 0.4) 0%, transparent 70%)"
                            filter="blur(60px)"
                            animate={{
                                scale: [1, 1.1, 1],
                                x: [0, 20, 0],
                                y: [0, 30, 0],
                            }}
                            transition={{
                                duration: 8,
                                repeat: Infinity,
                                ease: "easeInOut",
                            }}
                        />

                        {/* Minimal corner accents */}
                        <Box
                            position="absolute"
                            top="5%"
                            left="5%"
                            width="80px"
                            height="80px"
                            borderTop="2px solid"
                            borderLeft="2px solid"
                            borderColor="gray.300"
                        />

                        <Box
                            position="absolute"
                            bottom="5%"
                            right="5%"
                            width="80px"
                            height="80px"
                            borderBottom="2px solid"
                            borderRight="2px solid"
                            borderColor="gray.300"
                        />

                        {/* Driver Name Background */}
                        <MotionHeading
                            position="absolute"
                            top="50%"
                            left="50%"
                            zIndex={1}
                            fontSize={{ base: '5rem', md: '11rem', lg: '15rem' }}
                            fontWeight="900"
                            textTransform="uppercase"
                            color="gray.800"
                            whiteSpace="nowrap"
                            letterSpacing="-0.02em"
                            style={{
                                x: '-50%',
                                y: '-50%',
                                translateY: textY,
                                opacity: textOpacity,
                                scale: textSize,
                            }}
                            initial={{
                                opacity: 0,
                                scale: 1.2,
                                filter: "blur(10px)",
                            }}
                            animate={{
                                opacity: 0.12,
                                scale: 1,
                                filter: "blur(0px)",
                            }}
                            transition={{
                                type: "spring",
                                bounce: 0.40,
                                damping: 80,
                                stiffness: 80,
                                mass: 1,
                                visualDuration: 0.1,
                                delay: 0.4,
                            }}
                        >
                            {winnerName}
                        </MotionHeading>

                        {/* Season Winner Text */}
                        <MotionText
                            position="absolute"
                            top="50%"
                            left="50%"
                            zIndex={3}
                            fontSize={{ base: '1.2rem', md: '1.6rem', lg: '2rem' }}
                            fontWeight="600"
                            textTransform="uppercase"
                            color="gray.800"
                            whiteSpace="nowrap"
                            letterSpacing="0.3em"
                            style={{
                                x: '-50%',
                                y: '-50%',
                                translateY: seasonWinnerY,
                                opacity: seasonWinnerOpacity,
                            }}
                        >
                            SEASON WINNER
                        </MotionText>

                        {/* Elegant Frame*/}
                        <MotionBox
                            position="absolute"
                            bottom="8%"
                            left="50%"
                            width={{ base: '90%', md: '55%', lg: '45%' }}
                            height="75%"
                            zIndex={1}
                            style={{
                                x: '-50%',
                                scale: frameScale,
                                y: frameY,
                            }}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, delay: 0.1 }}
                        >
                            {/* Main frame */}
                            <Box
                                position="absolute"
                                top="0"
                                left="0"
                                right="0"
                                bottom="0"
                                border="2px solid"
                                borderColor="gray.300"
                                borderRadius="lg"
                                boxShadow="0 10px 40px rgba(0,0,0,0.06)"
                            />

                            {/* Inner frame */}
                            <Box
                                position="absolute"
                                top="8px"
                                left="8px"
                                right="8px"
                                bottom="8px"
                                border="1px solid"
                                borderColor="gray.200"
                                borderRadius="md"
                            />

                            {/* Corner accents */}
                            <Box position="absolute" top="-2px" left="-2px" width="50px" height="50px" borderTop="4px solid" borderLeft="4px solid" borderColor="gray.800" />
                            <Box position="absolute" top="-2px" right="-2px" width="50px" height="50px" borderTop="4px solid" borderRight="4px solid" borderColor="gray.800" />
                            <Box position="absolute" bottom="-2px" left="-2px" width="50px" height="50px" borderBottom="4px solid" borderLeft="4px solid" borderColor="gray.800" />
                            <Box position="absolute" bottom="-2px" right="-2px" width="50px" height="50px" borderBottom="4px solid" borderRight="4px solid" borderColor="gray.800" />

                            {/* Small decorative dots */}
                            <Box position="absolute" top="15px" left="15px" width="4px" height="4px" bg="gray.800" borderRadius="50%" />
                            <Box position="absolute" top="15px" right="15px" width="4px" height="4px" bg="gray.800" borderRadius="50%" />
                            <Box position="absolute" bottom="15px" left="15px" width="4px" height="4px" bg="gray.800" borderRadius="50%" />
                            <Box position="absolute" bottom="15px" right="15px" width="4px" height="4px" bg="gray.800" borderRadius="50%" />
                        </MotionBox>

                        {/* Driver Image*/}
                        <MotionImage
                            src={mainImageUrl}
                            alt={winnerName}
                            position="absolute"
                            bottom="0"
                            left="50%"
                            height={{ base: '62vh', md: '78vh' }}
                            width="auto"
                            objectFit="contain"
                            zIndex={2}
                            filter="drop-shadow(0 15px 35px rgba(0, 0, 0, 0.15))"
                            style={{
                                x: '-50%',
                                scale: imageScale,
                                y: imageY,
                            }}
                            initial={{ opacity: 0, y: 50 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.1 }}
                        />

                        {/* Scroll indicator */}
                        <MotionBox
                            position="absolute"
                            bottom="30px"
                            left="50%"
                            transform="translateX(-50%)"
                            zIndex={3}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1, y: [0, 8, 0] }}
                            transition={{ opacity: { delay: 1 }, y: { duration: 2, repeat: Infinity } }}
                        >
                            <VStack spacing={2}>
                                <Box w="1px" h="30px" bg="gray.400" />
                                <Text color="black.500" fontSize="xs" fontWeight="500" letterSpacing="widest">
                                    SCROLL
                                </Text>
                            </VStack>
                        </MotionBox>
                    </Box>

                    {/* Results Section */}
                    <Box bg="white" py={20} position="relative">
                        <Container maxW="container.xl">
                            <MotionBox
                                pt={4}
                                pb={10}
                                initial={{ opacity: 0, y: 40 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, amount: 0.3 }}
                                transition={{ duration: 0.6 }}
                            >
                                <VStack spacing={3} mb={12}>
                                    <Text
                                        fontSize="xs"
                                        fontWeight="600"
                                        color="gray.500"
                                        letterSpacing="widest"
                                        textTransform="uppercase"
                                    >
                                        Probability Standings
                                    </Text>
                                    <Heading
                                        fontSize={{ base: '2xl', md: '3xl' }}
                                        fontWeight="700"
                                        color="gray.800"
                                    >
                                        Championship Results
                                    </Heading>
                                </VStack>

                                <ResultsTable probabilities={successData.probabilities} />
                            </MotionBox>
                        </Container>
                    </Box>
                </MotionBox>
            );
        }

        return (
            <MotionBox
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                {/* Hero Section styling */}
                <Box
                    position="relative"
                    width="100%"
                    height={{ base: '85vh', md: '92vh' }}
                    overflow="hidden"
                    bg="linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%)"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                >
                    <Box
                        position="absolute"
                        top="0"
                        left="0"
                        right="0"
                        bottom="0"
                        opacity={0.03}
                        backgroundImage="linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)"
                        backgroundSize="50px 50px"
                    />

                    <Box
                        position="absolute"
                        top="0"
                        left="0"
                        right="0"
                        bottom="0"
                        bg="radial-gradient(ellipse at center, transparent 70%, rgba(25, 25, 25, 0.1) 100%)"
                        pointerEvents="none"
                    />

                    <SubtleParticles />

                    <MotionBox
                        position="absolute"
                        top="20%"
                        right="10%"
                        width="400px"
                        height="400px"
                        borderRadius="50%"
                        bg="radial-gradient(circle, rgba(229, 229, 229, 0.4) 0%, transparent 70%)"
                        filter="blur(60px)"
                        animate={{
                            scale: [1, 1.1, 1],
                            x: [0, 20, 0],
                            y: [0, 30, 0],
                        }}
                        transition={{
                            duration: 8,
                            repeat: Infinity,
                            ease: "easeInOut",
                        }}
                    />

                    <Box
                        position="absolute"
                        top="5%"
                        left="5%"
                        width="80px"
                        height="80px"
                        borderTop="2px solid"
                        borderLeft="2px solid"
                        borderColor="gray.300"
                    />

                    <Box
                        position="absolute"
                        bottom="5%"
                        right="5"
                        width="80px"
                        height="80px"
                        borderBottom="2px solid"
                        borderRight="2px solid"
                        borderColor="gray.30Services"
                    />

                    <MotionBox
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        textAlign={"center"}
                        zIndex={2}
                        p={8}
                    >
                        <Heading
                            as="h1"
                            fontSize={{ base: '3xl', md: '5xl' }}
                            fontWeight="800"
                            color="gray.800"
                            letterSpacing="tight"
                        >
                            Championship Simulator
                        </Heading>
                        <Text
                            fontSize={{ base: 'md', md: 'lg' }}
                            color="gray.600"
                            mt={4}
                            maxW="lg"
                        >
                            Click the "Simulate" button in the header to run the
                            championship simulation and see the probability
                            standings.
                        </Text>
                    </MotionBox>
                </Box>
            </MotionBox>
        );

    };

    return (
        <Box textAlign="center" minHeight="100vh" position="relative" bg="white">

            <MotionBox
                position="sticky"
                top={0}
                zIndex={10}
                bg="rgba(0, 0, 0, 0.8)"
                backdropFilter="blur(10px)"
                borderBottom="1px solid"
                borderColor="gray.200"
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Container maxW="container.xl">
                    <Box display="flex" justifyContent="space-between" alignItems="center" py={5}>
                        <Heading
                            fontSize={{ base: '20px', md: '30px' }}
                            fontWeight="700"
                            color="white"
                            letterSpacing="tight"
                            onClick={handleLogoClick}
                            cursor="pointer"
                        >
                            REDLINE
                        </Heading>
                        <Button
                            bg="whitesmoke"
                            color="black"
                            onClick={handleSimulateClick}
                            isLoading={isLoading || isRefetching} //
                            fontWeight="600"
                            size={{ base: 'sm', md: 'md' }}
                            px={6}
                            _hover={{
                                bg: "whitesmoke",
                                transform: 'translateY(-2px)',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                            }}
                            transition="all 0.2s"
                        >
                            Simulate
                        </Button>
                    </Box>
                </Container>
            </MotionBox>

            <Box>{renderContent()}</Box>
        </Box>
    );
}

export default LandingPage;