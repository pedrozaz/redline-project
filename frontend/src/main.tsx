import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChakraProvider } from "@chakra-ui/react"

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>

        <QueryClientProvider client={queryClient}>

            {/*@ts-ignore*/}
            <ChakraProvider>
                <App />
            </ChakraProvider>

        </QueryClientProvider>

    </React.StrictMode>,
)
