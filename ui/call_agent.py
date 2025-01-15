from fasthtml.common import *
import json
import boto3

# Set up AWS Step Functions client
stepfunctions = boto3.client('stepfunctions')

# Set up the app with Tailwind CSS for styling
tlink = Script(src="https://cdn.tailwindcss.com")
app = FastHTML(hdrs=(tlink,))

def format_tool_result(content):
    """Helper function to format tool results consistently"""
    try:
        result = json.loads(content)
        if isinstance(result, dict) and 'answer' in result:
            answer_lines = result['answer'].split('\n')
            return Div(
                *[P(line, cls="mb-2 break-words") for line in answer_lines if line.strip()],
                cls="bg-blue-50 p-3 rounded my-2"
            )
        else:
            return P(
                json.dumps(result, indent=2),
                cls="font-mono text-sm whitespace-pre-wrap break-words bg-blue-50 p-3 rounded"
            )
    except json.JSONDecodeError:
        return P(content, cls="break-words")

def ChatMessage(msg):
    def render_content(content):
        if isinstance(content, str):
            return [P(content, cls="break-words")]
        if isinstance(content, list):
            rendered_content = []
            for item in content:
                if item.get('type') == 'text':
                    rendered_content.append(P(item['text'], cls="break-words"))
                elif item.get('type') == 'tool_use':
                  
                    rendered_content.append(
                        Div(
                            P("🔧 Using tool: " + item['name'], cls="font-semibold"),
                            P(json.dumps(item['input'], indent=2), 
                              cls="font-mono text-sm whitespace-pre-wrap break-words"),
                            cls="bg-gray-700 text-white p-3 rounded my-2"
                        )
                    )
                elif item.get('type') == 'tool_result':
                    try:
                        content = item['content']
                        
                        # Check if content is a string and looks like a URL
                        if isinstance(content, str) and (content.startswith('http://') or content.startswith('https://')):
                            # For URLs that likely point to HTML content
                            if '.html' in content:
                                rendered_content.append(
                                    Iframe(
                                        src=content,
                                        cls="w-full h-96 border-0 rounded",
                                    )
                                )
                                continue
                        
                        # Handle other cases as before
                        if isinstance(content, (dict, list)):
                            result = content
                        else:
                            result = json.loads(content)
                            
                        # Check if content is a schema definition (dict with lists of column definitions)
                        if (isinstance(result, dict) and 
                            all(isinstance(v, list) and 
                                all(isinstance(col, list) and len(col) >= 3 
                                    for col in v) 
                                for v in result.values())):
                            
                            table_sections = []
                            
                            # Create a table for each schema
                            for table_name, columns in result.items():
                                # Create table header
                                header_row = Tr(
                                    Th("Column Name", cls="px-4 py-2 bg-gray-700 text-white"),
                                    Th("Type", cls="px-4 py-2 bg-gray-700 text-white"),
                                    Th("Nullable", cls="px-4 py-2 bg-gray-700 text-white"),
                                    Th("Default", cls="px-4 py-2 bg-gray-700 text-white"),
                                )
                            
                                # Create table rows
                                rows = []
                                for col in columns:
                                    # col format: [index, name, type, nullable, default, ...]
                                    nullable = "NULL" if col[3] == 0 else "NOT NULL"
                                    default = str(col[4]) if col[4] is not None else "None"
                                    
                                    row = Tr(
                                        Td(col[1], cls="px-4 py-2 border-t font-medium text-gray-900"),
                                        Td(col[2], cls="px-4 py-2 border-t font-mono text-sm text-gray-900"),
                                        Td(nullable, cls="px-4 py-2 border-t text-sm text-gray-900"),
                                        Td(default, cls="px-4 py-2 border-t text-sm text-gray-900"),
                                    )
                                    rows.append(row)
                                
                                # Create table with title
                                table_section = Div(
                                    H3(f"Table: {table_name}", 
                                       cls="text-lg font-semibold mb-2 text-gray-900"),
                                    Table(
                                        header_row,
                                        *rows,
                                        cls="min-w-full bg-white rounded shadow-md overflow-hidden"
                                    ),
                                    cls="bg-gray-100 p-4 rounded"
                                )
                                table_sections.append(table_section)
                            
                            # Add all table sections to a container div
                            rendered_content.append(
                                Div(
                                    *table_sections,
                                    cls="space-y-6"
                                )
                            )
                            continue
                            
                        # Check if content is a list of dictionaries (table-like data)
                        if (isinstance(result, list) and 
                            len(result) > 0 and 
                            isinstance(result[0], dict)):
                            
                            # Get headers from the first object's keys
                            headers = list(result[0].keys())
                            
                            # Create table header
                            header_row = Tr(*[Th(header.replace('_', ' ').title(), 
                                              cls="px-4 py-2") 
                                           for header in headers])
                            
                            # Create table rows
                            rows = []
                            for item in result:
                                row = Tr(*[Td(str(item.get(header, '')), 
                                           cls="px-4 py-2 border-t") 
                                         for header in headers])
                                rows.append(row)
                            
                            # Combine into table
                            rendered_content.append(
                                Table(
                                    header_row,
                                    *rows,
                                    cls="min-w-full bg-gray rounded shadow overflow-hidden"
                                )
                            )
                            continue


                        if isinstance(result, dict) and 'answer' in result:
                            answer_lines = result['answer'].split('\n')
                            rendered_content.append(
                                Div(
                                    *[P(line, cls="mb-2") for line in answer_lines if line.strip()],
                                    cls="bg-gray-50 text-gray-900 p-3 rounded my-2"
                                )
                            )
                        else:
                            rendered_content.append(
                                P(json.dumps(result, indent=2), 
                                  cls="font-mono text-sm whitespace-pre-wrap bg-gray-50 text-gray-900 p-3 rounded")
                            )
                    except json.JSONDecodeError:
                        rendered_content.append(P(str(item['content']), cls="break-words"))
            return rendered_content
        return []

    # Define base and role-specific classes separately for better readability
    base_class = "max-w-[80%] rounded-lg p-4 my-2"
    role_class = (
        "bg-blue-500 text-blue-50 ml-auto" if msg['role'] == 'user' 
        else "bg-gray-100 text-gray-900"
    )
    
    content_class = "text-inherit"
    
    return Div(
        Div(
            Div(msg['role'].title(), cls="font-bold mb-1"),
            *[Div(content, cls=content_class) for content in render_content(msg['content'])],
            cls=f"{base_class} {role_class}"
        ),
        cls="w-full"
    )


# Define the conversation data
messages = []

def list_tagged_step_functions():
    """
    List Step Functions that have the tag application=ai-agents
    """
    paginator = stepfunctions.get_paginator('list_state_machines')
    tagged_state_machines = []

    # Iterate through all pages of state machines
    for page in paginator.paginate():
        for state_machine in page['stateMachines']:
            # Get tags for each state machine
            tags_response = stepfunctions.list_tags_for_resource(
                resourceArn=state_machine['stateMachineArn']
            )
            # print(tags_response)
            # Check if the required tag exists
            tags = tags_response.get('tags', [])
            for tag in tags:
                if tag.get('key') == 'application' and tag.get('value') == 'ai-agents':
                    tagged_state_machines.append({
                        'name': state_machine['name'],
                        'arn': state_machine['stateMachineArn'],
                        'creationDate': state_machine['creationDate'].isoformat(),
                        'tags': tags
                    })
                    break

    return tagged_state_machines

# Add a form to start state machine execution
def ExecutionForm():
    step_functions = list_tagged_step_functions()
    # print(step_functions)
    state_machine_options = [Option(sf['name'], value=sf['arn'] ) for sf in step_functions]
    state_machine_options.insert(0, Option("Select a state machine", value=""))
    print(state_machine_options)
    return Form(
        Group(
            Select(
                *state_machine_options,
                id="state_machine_arn", 
                name="state_machine_arn",
                cls="w-full p-2 border rounded"
            ),
            Input(id="execution_name", name="execution_name",
                  placeholder="Execution Name (optional)",
                  cls="w-full p-2 border rounded mt-2"),
            Input(id="input", name="input",
                  placeholder="User Input",
                    cls="w-full p-2 border rounded mt-2",
                  type="text"),
            Button("Start Execution", 
                   cls="bg-green-500 text-white px-4 py-2 rounded mt-2 hover:bg-green-600"),
        ),
        hx_post="/start-execution",
        hx_target="#execution-result",
        cls="mb-4"
    )

def ExecutionStatus(execution_arn):
    try:
        response = stepfunctions.describe_execution(executionArn=execution_arn)
        status = response['status']
        
        status_styles = {
            'RUNNING': 'bg-blue-50 text-blue-700',
            'SUCCEEDED': 'bg-green-50 text-green-700',
            'FAILED': 'bg-red-50 text-red-700',
            'TIMED_OUT': 'bg-yellow-50 text-yellow-700',
            'ABORTED': 'bg-gray-50 text-gray-700'
        }
        status_class = status_styles.get(status, 'bg-gray-50 text-gray-700')
        
        # Create the content without the polling wrapper when complete
        inner_content = [
            H2("Execution Status", cls="text-lg font-bold"),
            P(f"Status: {status}", cls=f"font-bold {status_class} inline-block px-2 py-1 rounded"),
            P(f"Started: {response['startDate']}", cls="mt-1"),
        ]
        
        if status != 'RUNNING':
            inner_content.append(P(f"Stopped: {response['stopDate']}", cls="mt-1"))
            
            if status == 'SUCCEEDED' and 'output' in response:
                try:
                    output = response['output']
                    if isinstance(output, str):
                        output = json.loads(output)
                    
                    if isinstance(output, dict) and 'messages' in output:
                        messages = output['messages']
                        if messages:
                            inner_content.extend([
                                H3("Conversation:", cls="text-lg font-bold mt-4"),
                                *[ChatMessage(msg) for msg in messages]
                            ])
                        
                except Exception as e:
                    inner_content.append(
                        P(f"Could not process execution output: {str(e)}", 
                          cls="text-red-600 mt-2")
                    )
            elif status == 'FAILED':
                inner_content.append(
                    P(f"Error: {response.get('error', 'Unknown error')}", 
                      cls="text-red-600 mt-2")
                )

        # For running state, wrap in polling div
        if status == 'RUNNING':
            return Div(
                Div(*inner_content, cls="p-4 border rounded"),
                id="execution-result",
                hx_get=f'/execution-status/{execution_arn}',
                hx_trigger='every 2s',
                hx_target='#execution-result'
            )
        else:
            # For completed state, return without polling attributes
            return Div(
                *inner_content,
                id="execution-result",
                cls="p-4 border rounded"
            )
        
    except Exception as e:
        return Div(
            P(f"Error checking execution status: {str(e)}", cls="text-red-600"),
            cls="p-4 bg-red-50 rounded"
        )

@app.route("/execution-status/{execution_arn}")
def get_execution_status(execution_arn: str):
    return ExecutionStatus(execution_arn)

@app.route("/start-execution")
def post(state_machine_arn: str, execution_name: str = None, input: str = "What can you do?"):
    try:
        # Validate input JSON
        input_dict = {
            "messages": [
                {
                "role": "user",
                "content": input
                }
            ]
        }
        
        # Start execution
        kwargs = {
            'stateMachineArn': state_machine_arn,
            'input': json.dumps(input_dict)
        }
        if execution_name:
            kwargs['name'] = execution_name

        response = stepfunctions.start_execution(**kwargs)
        
        # Return initial status with polling
        return ExecutionStatus(response['executionArn'])
        
    except json.JSONDecodeError:
        return Div(
            P("Invalid JSON input", cls="text-red-600"),
            cls="p-4 bg-red-50 rounded"
        )
    except Exception as e:
        return Div(
            P(f"Error: {str(e)}", cls="text-red-600"),
            cls="p-4 bg-red-50 rounded"
        )

@app.route("/")
def get():
    return Titled("State Machine Execution",
        Container(
            H1("AWS Step Functions Execution", cls="text-2xl font-bold mb-6"),
            ExecutionForm(),
            Div(id="execution-result", cls="mt-4"),
            # Chat display below
            Div(
                *[ChatMessage(msg) for msg in messages],
                cls="max-w-4xl mx-auto space-y-2 mt-8"
            )
        )
    )

serve()