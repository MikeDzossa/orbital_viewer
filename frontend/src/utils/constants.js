// Static mapping planetName -> relative URL (public folder served as root)
export const STAR_TEXTURES = {
    Sun: '/textures/planets/Sun.jpg',
    Mercury: '/textures/planets/Mercury.jpg',
    Venus: '/textures/planets/Venus.jpg',
    Earth: '/textures/planets/Earth.jpg',
    Mars: '/textures/planets/Mars.jpg',
    Jupiter: '/textures/planets/Jupiter.jpg',
    Saturn: '/textures/planets/Saturn.jpg',
    Uranus: '/textures/planets/Uranus.jpg',
    Neptune: '/textures/planets/Neptune.jpg',
    Pluto: '/textures/planets/Pluto.jpg'
};

export const STAR_SCALES = {
    Sun: 3.5,
    Mercury: 0.25,
    Venus: 0.55,
    Earth: 0.6,
    Mars: 0.4,
    Jupiter: 1.4,
    Saturn: 1.2,
    Uranus: 0.9,
    Neptune: 0.9,
    Pluto: 0.22
};

export const STAR_DEFAULT_COLORS = {
    Sun: 0xffff66,
    Mercury: 0xffcc66,
    Venus: 0xff9966,
    Earth: 0x66ccff,
    Mars: 0xcc6666,
    Jupiter: 0x99ffcc,
    Saturn: 0xcc99ff,
    Uranus: 0x6699ff,
    Neptune: 0xff6699,
    Pluto: 0xcccccc
};

// Global uniform downscale for visual clarity vs orbit distances
// Adjust this if planets overlap or appear too large relative to their orbits.
export const SIZE_SCALE = 0.05; // shrink everything to 10% of prior size