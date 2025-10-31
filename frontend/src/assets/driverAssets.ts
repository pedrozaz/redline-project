interface DriverAsset {
    main: string;
    helmet: string;
}

export const driverAssetMap: Record<string, DriverAsset> = {
    'Lando Norris': {
        main: 'norris.avif',
        helmet: 'norris-helmet.png',
    }
}

export const placeholderAssets: DriverAsset = {
    main: 'norris.avif',
    helmet: 'norris-helmet.png',
}
