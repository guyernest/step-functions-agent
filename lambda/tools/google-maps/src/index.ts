import { Handler } from 'aws-lambda';
import { getSecret } from '@aws-lambda-powertools/parameters/secrets';
import { Logger } from '@aws-lambda-powertools/logger';

const logger = new Logger({ serviceName: 'Google Maps Tools' });

// Response interfaces
interface GoogleMapsResponse {
    status: string;
    error_message?: string;
}

interface GeocodeResponse extends GoogleMapsResponse {
    results: Array<{
        place_id: string;
        formatted_address: string;
        geometry: {
            location: {
                lat: number;
                lng: number;
            }
        };
        address_components: Array<{
            long_name: string;
            short_name: string;
            types: string[];
        }>;
    }>;
}

interface PlacesSearchResponse extends GoogleMapsResponse {
    results: Array<{
        name: string;
        place_id: string;
        formatted_address: string;
        geometry: {
            location: {
                lat: number;
                lng: number;
            }
        };
        rating?: number;
        types: string[];
    }>;
}

interface PlaceDetailsResponse extends GoogleMapsResponse {
    result: {
        name: string;
        place_id: string;
        formatted_address: string;
        formatted_phone_number?: string;
        website?: string;
        rating?: number;
        reviews?: Array<{
            author_name: string;
            rating: number;
            text: string;
            time: number;
        }>;
        opening_hours?: {
            weekday_text: string[];
            open_now: boolean;
        };
        geometry: {
            location: {
                lat: number;
                lng: number;
            }
        };
    };
}

interface DistanceMatrixResponse extends GoogleMapsResponse {
    origin_addresses: string[];
    destination_addresses: string[];
    rows: Array<{
        elements: Array<{
            status: string;
            duration: {
                text: string;
                value: number;
            };
            distance: {
                text: string;
                value: number;
            };
        }>;
    }>;
}

interface ElevationResponse extends GoogleMapsResponse {
    results: Array<{
        elevation: number;
        location: {
            lat: number;
            lng: number;
        };
        resolution: number;
    }>;
}

interface DirectionsResponse extends GoogleMapsResponse {
    routes: Array<{
        summary: string;
        legs: Array<{
            distance: {
                text: string;
                value: number;
            };
            duration: {
                text: string;
                value: number;
            };
            steps: Array<{
                html_instructions: string;
                distance: {
                    text: string;
                    value: number;
                };
                duration: {
                    text: string;
                    value: number;
                };
                travel_mode: string;
            }>;
        }>;
    }>;
}

// Global API key
let GOOGLE_MAPS_API_KEY: string;

async function initializeApiKey(): Promise<void> {
    try {
        const apiKeySecret = await getSecret("/ai-agent/GOOGLE_MAPS_API_KEY");
        if (!apiKeySecret) {
            throw new Error("Failed to retrieve secret from Secrets Manager");
        }
        GOOGLE_MAPS_API_KEY = JSON.parse(apiKeySecret.toString())["GOOGLE_MAPS_API_KEY"];
        logger.info("API key initialized successfully");
    } catch (error) {
        logger.error('Failed to initialize API key', { error });
        throw error;
    }
}

// Tool definitions
const GEOCODE_TOOL = {
    name: "maps_geocode",
    description: "Convert an address into geographic coordinates",
    inputSchema: {
        type: "object",
        properties: {
            address: {
                type: "string",
                description: "The address to geocode"
            }
        },
        required: ["address"]
    }
};

const REVERSE_GEOCODE_TOOL = {
    name: "maps_reverse_geocode",
    description: "Convert coordinates into an address",
    inputSchema: {
        type: "object",
        properties: {
            latitude: {
                type: "number",
                description: "Latitude coordinate"
            },
            longitude: {
                type: "number",
                description: "Longitude coordinate"
            }
        },
        required: ["latitude", "longitude"]
    }
};

const SEARCH_PLACES_TOOL = {
    name: "maps_search_places",
    description: "Search for places using Google Places API",
    inputSchema: {
        type: "object",
        properties: {
            query: {
                type: "string",
                description: "Search query"
            },
            location: {
                type: "object",
                properties: {
                    latitude: { type: "number" },
                    longitude: { type: "number" }
                },
                description: "Optional center point for the search"
            },
            radius: {
                type: "number",
                description: "Search radius in meters (max 50000)"
            }
        },
        required: ["query"]
    }
};

const PLACE_DETAILS_TOOL = {
    name: "maps_place_details",
    description: "Get detailed information about a specific place",
    inputSchema: {
        type: "object",
        properties: {
            place_id: {
                type: "string",
                description: "The place ID to get details for"
            }
        },
        required: ["place_id"]
    }
};

const DISTANCE_MATRIX_TOOL = {
    name: "maps_distance_matrix",
    description: "Calculate travel distance and time for multiple origins and destinations",
    inputSchema: {
        type: "object",
        properties: {
            origins: {
                type: "array",
                items: { type: "string" },
                description: "Array of origin addresses or coordinates"
            },
            destinations: {
                type: "array",
                items: { type: "string" },
                description: "Array of destination addresses or coordinates"
            },
            mode: {
                type: "string",
                description: "Travel mode (driving, walking, bicycling, transit)",
                enum: ["driving", "walking", "bicycling", "transit"]
            }
        },
        required: ["origins", "destinations"]
    }
};

const ELEVATION_TOOL = {
    name: "maps_elevation",
    description: "Get elevation data for locations on the earth",
    inputSchema: {
        type: "object",
        properties: {
            locations: {
                type: "array",
                items: {
                    type: "object",
                    properties: {
                        latitude: { type: "number" },
                        longitude: { type: "number" }
                    },
                    required: ["latitude", "longitude"]
                },
                description: "Array of locations to get elevation for"
            }
        },
        required: ["locations"]
    }
};

const DIRECTIONS_TOOL = {
    name: "maps_directions",
    description: "Get directions between two points",
    inputSchema: {
        type: "object",
        properties: {
            origin: {
                type: "string",
                description: "Starting point address or coordinates"
            },
            destination: {
                type: "string",
                description: "Ending point address or coordinates"
            },
            mode: {
                type: "string",
                description: "Travel mode (driving, walking, bicycling, transit)",
                enum: ["driving", "walking", "bicycling", "transit"]
            }
        },
        required: ["origin", "destination"]
    }
};

const MAPS_TOOLS = [
    GEOCODE_TOOL,
    REVERSE_GEOCODE_TOOL,
    SEARCH_PLACES_TOOL,
    PLACE_DETAILS_TOOL,
    DISTANCE_MATRIX_TOOL,
    ELEVATION_TOOL,
    DIRECTIONS_TOOL,
] as const;

// API handlers
async function handleGeocode(address: string) {
    const url = new URL("https://maps.googleapis.com/maps/api/geocode/json");
    url.searchParams.append("address", address);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);
    const response = await fetch(url.toString());
    const data = await response.json() as GeocodeResponse;

    if (data.status !== "OK") {
        return `Geocoding failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                location: data.results[0].geometry.location,
                formatted_address: data.results[0].formatted_address,
                place_id: data.results[0].place_id
            }, null, 2)
        
}

async function handleReverseGeocode(latitude: number, longitude: number) {
    const url = new URL("https://maps.googleapis.com/maps/api/geocode/json");
    url.searchParams.append("latlng", `${latitude},${longitude}`);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    const response = await fetch(url.toString());
    const data = await response.json() as GeocodeResponse;

    if (data.status !== "OK") {
        return `Reverse geocoding failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                formatted_address: data.results[0].formatted_address,
                place_id: data.results[0].place_id,
                address_components: data.results[0].address_components
            }, null, 2)
        
}

async function handlePlaceSearch(
    query: string,
    location?: { latitude: number; longitude: number },
    radius?: number
) {
    const url = new URL("https://maps.googleapis.com/maps/api/place/textsearch/json");
    url.searchParams.append("query", query);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    if (location) {
        url.searchParams.append("location", `${location.latitude},${location.longitude}`);
    }
    if (radius) {
        url.searchParams.append("radius", radius.toString());
    }

    const response = await fetch(url.toString());
    const data = await response.json() as PlacesSearchResponse;

    if (data.status !== "OK") {
        return `Place search failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                places: data.results.map((place) => ({
                    name: place.name,
                    formatted_address: place.formatted_address,
                    location: place.geometry.location,
                    place_id: place.place_id,
                    rating: place.rating,
                    types: place.types
                }))
            }, null, 2)
        
}

async function handlePlaceDetails(place_id: string) {
    const url = new URL("https://maps.googleapis.com/maps/api/place/details/json");
    url.searchParams.append("place_id", place_id);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    const response = await fetch(url.toString());
    const data = await response.json() as PlaceDetailsResponse;

    if (data.status !== "OK") {
        return `Place details request failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                name: data.result.name,
                formatted_address: data.result.formatted_address,
                location: data.result.geometry.location,
                formatted_phone_number: data.result.formatted_phone_number,
                website: data.result.website,
                rating: data.result.rating,
                reviews: data.result.reviews,
                opening_hours: data.result.opening_hours
            }, null, 2)
}
async function handleDistanceMatrix(
    origins: string[],
    destinations: string[],
    mode: "driving" | "walking" | "bicycling" | "transit" = "driving"
) {
    const url = new URL("https://maps.googleapis.com/maps/api/distancematrix/json");
    url.searchParams.append("origins", origins.join("|"));
    url.searchParams.append("destinations", destinations.join("|"));
    url.searchParams.append("mode", mode);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    const response = await fetch(url.toString());
    const data = await response.json() as DistanceMatrixResponse;

    if (data.status !== "OK") {
        return `Distance matrix request failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                origin_addresses: data.origin_addresses,
                destination_addresses: data.destination_addresses,
                results: data.rows.map((row) => ({
                    elements: row.elements.map((element) => ({
                        status: element.status,
                        duration: element.duration,
                        distance: element.distance
                    }))
                }))
            }, null, 2)
}

async function handleElevation(locations: Array<{ latitude: number; longitude: number }>) {
    const url = new URL("https://maps.googleapis.com/maps/api/elevation/json");
    const locationString = locations
        .map((loc) => `${loc.latitude},${loc.longitude}`)
        .join("|");
    url.searchParams.append("locations", locationString);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    const response = await fetch(url.toString());
    const data = await response.json() as ElevationResponse;

    if (data.status !== "OK") {
        return `Elevation request failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                results: data.results.map((result) => ({
                    elevation: result.elevation,
                    location: result.location,
                    resolution: result.resolution
                }))
            }, null, 2)
}

async function handleDirections(
    origin: string,
    destination: string,
    mode: "driving" | "walking" | "bicycling" | "transit" = "driving"
) {
    const url = new URL("https://maps.googleapis.com/maps/api/directions/json");
    url.searchParams.append("origin", origin);
    url.searchParams.append("destination", destination);
    url.searchParams.append("mode", mode);
    url.searchParams.append("key", GOOGLE_MAPS_API_KEY);

    const response = await fetch(url.toString());
    const data = await response.json() as DirectionsResponse;

    if (data.status !== "OK") {
        return `Directions request failed: ${data.error_message || data.status}`
    }

    return JSON.stringify({
                routes: data.routes.map((route) => ({
                    summary: route.summary,
                    distance: route.legs[0].distance,
                    duration: route.legs[0].duration,
                    steps: route.legs[0].steps.map((step) => ({
                        instructions: step.html_instructions,
                        distance: step.distance,
                        duration: step.duration,
                        travel_mode: step.travel_mode
                    }))
                }))
            }, null, 2)
}

export const handler: Handler = async (event, context) => {

    // Initialize API key if not already set
    if (!GOOGLE_MAPS_API_KEY) {
        await initializeApiKey();
    }

    logger.info("Received event", { event });
    const tool_use = event
    const tool_name = tool_use["name"]
    try {
        let result: string
        switch (tool_name) {
          case "maps_geocode": {
            const { address } = tool_use.input as { address: string }
            result = await handleGeocode(address);
            break;
          }
    
          case "maps_reverse_geocode": {
            const { latitude, longitude } = tool_use.input as { latitude: number, longitude: number }
            result = await handleReverseGeocode(latitude, longitude);
            break;
          }
    
          case "maps_search_places": {
            const { query, location, radius } = tool_use.input as { 
                query: string;
                location?: { latitude: number; longitude: number };
                radius?: number;
            }
            result = await handlePlaceSearch(query, location, radius);
            break;
          }
    
          case "maps_place_details": {
            const { place_id } = tool_use.input as { place_id: string }
            result = await handlePlaceDetails(place_id);
            break;
          }
    
          case "maps_distance_matrix": {
            const { origins, destinations, mode } = tool_use.input as { 
                origins: string[], 
                destinations: string[], 
                mode?: "driving" | "walking" | "bicycling" | "transit"
            }
            result = await handleDistanceMatrix(origins, destinations, mode);
            break;
          }
    
          case "maps_elevation": {
            const { locations } = tool_use.input as { 
                locations: Array<{ latitude: number; longitude: number }>;
            }
            result = await handleElevation(locations);
            break;
          }
    
          case "maps_directions": {
            const { origin, destination, mode } = tool_use.input as { 
                origin: string;
                destination: string;
                mode?: "driving" | "walking" | "bicycling" | "transit";
            }
            result = await handleDirections(origin, destination, mode);
            break;
          }
    
          default:
            result = `Unknown tool: ${tool_name}`
        }
        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": result
        }
      } catch (error) {
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": `Error: ${error instanceof Error ? error.message : String(error)}`
        }
      }
};
