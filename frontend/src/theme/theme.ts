import { extendTheme, theme as baseTheme } from '@chakra-ui/react'

const colors = {
    brand: {
        red: '#E80020',
        white: '#FFFFFF',
        black: '#1A1A1A',
    },
    gray: {
        800: '#1A1A1A',
        700: '#2D2D2D',
    },
    red: {
        500: '#E80020',
    },
};

const fonts = {
    body: `'Roboto', ${baseTheme.fonts?.body}`,
    heading: `'Roboto', ${baseTheme.fonts?.heading}`,
};

export const redlineTheme = extendTheme({
    colors,
    fonts,
    styles:
        {
            global: {
                body: {
                    bg: 'brand.black',
                    color: 'brand.white',
                },
            },
        },
});