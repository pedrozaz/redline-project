import { extendTheme } from '@chakra-ui/react';

const colors = {
    brand: {
        red: '#E80020',
        white: '#FAFAFA',
        black: '#1A1A1A',
    },
    gray: {
        200: '#E2E2E2',
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

const fonts = {
    heading: "'Aldrich', sans-serif",
    body: "'Aldrich', sans-serif",
}

export const redlineTheme = extendTheme({
    colors,
    styles,
    fonts
});