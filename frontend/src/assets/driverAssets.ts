interface DriverAsset {
    main: string;
}

export const driverAssetMap: Record<string, DriverAsset> = {
    'Lando Norris': {
        main: 'norris.avif',
    }
}

export const placeholderAssets: DriverAsset = {
    main: 'norris.avif',
}
