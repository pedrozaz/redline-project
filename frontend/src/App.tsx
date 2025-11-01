import { ChakraProvider } from '@chakra-ui/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { redlineTheme as theme } from './theme/theme';
import LandingPage from './components/LandingPage';

const queryClient = new QueryClient();

function App() {
    return (
        <ChakraProvider theme={theme}>
            <QueryClientProvider client={queryClient}>
                <LandingPage />
            </QueryClientProvider>
        </ChakraProvider>
    );
}

export default App;