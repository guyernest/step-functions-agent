from fasthtml.common import *
import json

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
                    rendered_content.append(format_tool_result(item['content']))
            return rendered_content
        return []

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

def main():
    # Sample test messages
    test_messages = [
        {
            "role": "user",
            "content": "Hello! Can you help me with data analysis?"
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I'd be happy to help with your data analysis!"},
                {"type": "tool_use", "name": "analyze_data", "input": {"dataset": "sample.csv"}}
            ]
        },
        {
            "role": "assistant",
            "content": [
                {"type": "tool_result", "content": json.dumps({"answer": "Based on the analysis:\n- Point 1\n- Point 2"})}
            ]
        }
    ]

    # Set up the app with Tailwind CSS
    tlink = Script(src="https://cdn.tailwindcss.com")
    app = FastHTML(hdrs=(tlink,))

    # Create the HTML
    html = Titled("Chat Test Display",
        Container(
            H1("Chat Display Test", cls="text-2xl font-bold mb-6"),
            Div(
                *[ChatMessage(msg) for msg in test_messages],
                cls="max-w-4xl mx-auto space-y-2"
            )
        )
    )

    # Save to file
    with open('chat_test.html', 'w') as f:
        f.write(str(html))
    
    print("Test HTML has been generated in 'chat_test.html'")

if __name__ == "__main__":
    main()