import { Handler } from 'aws-lambda';
import { getSecret } from '@aws-lambda-powertools/parameters/secrets';
import { Logger } from '@aws-lambda-powertools/logger';
import fetch from 'node-fetch'
import { title } from 'process';

const logger = new Logger({ serviceName: 'EarthQuakeQueryTS' });

type EarthquakeFeature = {
    type: string;
    properties: {
        mag: number;
        place: string;
        time: number;
        updated: number;
        tz: number | null;
        url: string;
        detail: string;
        felt: number | null;
        cdi: number | null;
        mmi: number | null;
        alert: string | null;
        status: string;
        tsunami: number;
        sig: number;
        net: string;
        code: string;
        ids: string;
        sources: string;
        types: string;
        nst: number | null;
        dmin: number | null;
        rms: number;
        gap: number | null;
        magType: string;
        type: string;
        title: string;
    };
    geometry: {
        type: string;
        coordinates: [number, number, number];
    };
    id: string;
};

// Response interface
type EarthquakeResponse = {
    type: string;
    metadata: {
        generated: number;
        url: string;
        title: string;
        status: number;
        api: string;
        count: number;
    };
    features: EarthquakeFeature[];
};

// Tool definition
const EarthQuakeQueryTSTool = {
    name: "query_earthquakes",
    description: "Query interface to the USGS Earthquake Catalog API",
    inputSchema: {
        type: "object",
        properties: {
            start_date: {
                type: "string",
                description: "The start date of the query in YYYY-MM-DD format"
            },
            end_date: {
                type: "string",
                description: "The end date of the query in YYYY-MM-DD format"
            }
        },
        required: [
            "start_date",
            "end_date"
        ]
    }
};


async function EarthQuakeQueryTS(
    start_date: string,
    end_date: string
): Promise<string> {

    const params = {
        format: 'geojson',
        starttime: start_date,
        endtime: end_date,
        minmagnitude: "4.5",
    };

    const queryString = new URLSearchParams(params).toString();
    const url = `https://earthquake.usgs.gov/fdsnws/event/1/query?${queryString}`;

    try {
        const response = await fetch(url, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json() as EarthquakeResponse;
        logger.info("Data", { data });
        return JSON.stringify({
            title: data.metadata.title,
            earthquekes: data.features.map(earthquake => ({
                mag: earthquake.properties.mag,
                place: earthquake.properties.place,
                time: earthquake.properties.time,
                tsunami: earthquake.properties.tsunami,
                type: earthquake.properties.type,
                title: earthquake.properties.title,
            }))
        }, null, 2);

    } catch (error) {
        logger.error('Error fetching data:', { error });
        return JSON.stringify({
            error: `Error fetching earthquake data: ${error instanceof Error ? error.message : String(error)}`
        });
    }
}

exports.handler = async (event: any, context: any) => {

    logger.info("Received event", { event });
    const tool_use = event;
    const tool_name = tool_use["name"];

    try {
        let result: string;
        switch (tool_name) {
            case "query_earthquakes": {
                const { start_date, end_date } = tool_use.input as {
                    start_date: string,
                    end_date: string
                };
                result = await EarthQuakeQueryTS(
                    start_date,
                   end_date
                );
                logger.info("Result", { result });
                break;
            }
            default:
                result = JSON.stringify({
                    error: `Unknown tool: ${tool_name}`
                });
        }

        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        };
    } catch (error) {
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": JSON.stringify({
                error: error instanceof Error ? error.message : String(error)
            })
        };
    }
};