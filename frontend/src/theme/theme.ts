import { extendTheme } from '@chakra-ui/react';

const colors = {
    brand: {
        red: '#E80020',
        white: '#FAFAFA', // Branco Gelo
        black: '#1A1A1A', // Preto
    },
    gray: {
        200: '#E2E2E2', // Para o nome fade (claro)
        300: '#C9C9C9',
    },
    red: {
        500: '#E80020',
    },
};

const styles = {
    global: {
        body: {
            bg: 'brand.white',
            color: 'brand.black',
        },
    },
};

export const redlineTheme = extendTheme({
    colors,
    styles,
});