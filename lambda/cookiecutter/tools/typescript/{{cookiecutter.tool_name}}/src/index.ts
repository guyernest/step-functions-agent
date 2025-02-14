import { Handler } from 'aws-lambda';
import { getSecret } from '@aws-lambda-powertools/parameters/secrets';
import { Logger } from '@aws-lambda-powertools/logger';
import fetch from 'node-fetch'

const logger = new Logger({ serviceName: '{{cookiecutter.tool_name}}' });

// Response interface
type {{cookiecutter.tool_name}}Response {
    // Define the structure of your response here
    // For example:
    metadata: {
        title: string;
        status: number;
    };
    items: {
        title: string;
        time: string;
        type: string;
    }[];

}

// Tool definition
const {{cookiecutter.tool_name}} = {
    name: "{{cookiecutter.tool_name}}",
    description: "{{cookiecutter.tool_description}}",
    inputSchema: {
        type: "object",
        properties: {
            {{cookiecutter.input_param_name}}: {
                type: "string",
                description: "{{cookiecutter.input_param_description}}"
            }
        },
        required: ["{{cookiecutter.input_param_name}}"]
    }
};


async function {{cookiecutter.tool_name}}({{cookiecutter.input_param_name}}: string): string {

    try {
        // Your logic here
        // For example:
        const response = await fetch(`https://api.example.com/{{cookiecutter.tool_name}}`);
        
        const data = await response.json() as {{cookiecutter.tool_name}}Response;
        logger.info("Data", { data });
        return JSON.stringify({
            // Process your data here
            // For example:

            title: data.metadata.title,
            items: data.items.map(item => ({
                time: item.properties.time,
                type: item.properties.type,
                title: item.properties.title,
            }))
        }, null, 2);

        
    } catch (error) {
        logger.error('Error fetching books data:', { error });
        return JSON.stringify({
            error: `Error fetching books data: ${error instanceof Error ? error.message : String(error)}`
        });
    }
}

exports.handler = async (event:any, context:any) => {
    
    logger.info("Received event", { event });
    const tool_use = event;
    const tool_name = tool_use["name"];

    try {
        let result: string;
        switch (tool_name) {
            case "{{cookiecutter.tool_name}}": {
                const { {{cookiecutter.input_param_name}} } = tool_use.input as { 
                    {{cookiecutter.input_param_name}}: string 
                };
                result = await {{cookiecutter.tool_name}}({{cookiecutter.input_param_name}});
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