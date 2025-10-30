import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChakraProvider } from '@chakra-ui/react'
import { redlineTheme } from './theme/theme'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>

            <ChakraProvider theme={redlineTheme}>
                <App />
            </ChakraProvider>

        </QueryClientProvider>
    </React.StrictMode>,
)
