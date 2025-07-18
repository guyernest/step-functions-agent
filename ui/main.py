from fasthtml.common import *
import json

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
                    rendered_content.append(
                        Div(
                            P("📊 Tool Result:", cls="font-semibold mb-2"),
                            format_tool_result(item['content']),
                            cls="text-gray-900"
                        )
                    )
            return rendered_content
        return []

    # Handle case where user message is a tool result list
    if msg['role'] == 'user' and isinstance(msg['content'], list) and \
       all(item.get('type') == 'tool_result' for item in msg['content']):
        # Special formatting for user tool results
        base_class = "max-w-[80%] rounded-lg p-4 my-2 ml-auto bg-blue-500 text-blue-50"
        return Div(
            Div(
                Div("User Tool Result", cls="font-bold mb-1"),
                *[Div(
                    format_tool_result(item['content']),
                    cls="text-gray-900"
                  ) for item in msg['content']],
                cls=base_class
            ),
            cls="w-full"
        )

    # Regular message formatting
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
messages = [
    {
      "role": "user",
      "content": "recent news about Google"
    },
    {
      "role": "assistant",
      "content": [
        {
          "text": "I'll help you research recent news and developments about Google. Let me use the research company function to get this information.",
          "type": "text"
        },
        {
          "id": "toolu_01PipicaRSpq9Y8iZu2uXGHR",
          "input": {
            "company": "Google",
            "topics": [
              "recent news",
              "financial performance",
              "market position"
            ]
          },
          "name": "research_company",
          "type": "tool_use"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01PipicaRSpq9Y8iZu2uXGHR",
          "content": "{\n  \"company\": \"Google\",\n  \"information\": {\n    \"financial performance\": \"Google's financial performance for the third quarter of 2024 is strong. Revenues increased 15% year-over-year to $88.3 billion, driven by a 13% rise in Google Services to $76.5 billion and a 35% increase in Google Cloud to $11.4 billion, fueled by AI growth. Operating income rose 34%, and operating margin expanded by 4.5 percentage points to 32%. Net income and EPS also increased by 34% and 37%, respectively, to $2.12. CEO Sundar Pichai attributed the success to AI investments and ongoing efficiency improvements[1][2].\",\n    \"market position\": \"Google maintains a dominant position in the search market, with over 90% market share globally and 88% in the United States as of 2025[1][3]. The company processes an estimated 6.3 million searches per minute and accounts for 89.33% of the global search engine market[5]. Despite potential threats from AI-powered alternatives and specialized search platforms, Google's sophisticated algorithms and extensive user base continue to secure its leading position in web discovery[1][3].\",\n    \"recent news\": \"Google is focusing on 2025 as a critical year, heavily betting on artificial intelligence (AI) and Gemini to disrupt the existing landscape. Recent updates include the launch of Gemini 2.0 and the quantum computing chip Willow. Google TV is integrating new Gemini-powered AI features, enhancing user interaction. The January 2025 update for Pixel phones addresses multiple vulnerabilities and includes bug fixes and security patches. Additionally, Google is rolling out AI Overviews in Search and improving Android with Gemini Nano, which will enhance multimodal capabilities and accessibility features[1][3][4].\"\n  }\n}"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "text": "Let me summarize this information for you in a clear format.",
          "type": "text"
        },
        {
          "id": "toolu_01HyGb3KNm4XhuGMDHSwD7S6",
          "input": {
            "answer": "Here are the key recent developments about Google:\n\n🔍 Recent News & Developments:\n- Google has launched Gemini 2.0 and a new quantum computing chip called Willow\n- Google TV is getting new AI features powered by Gemini\n- The company released a January 2025 update for Pixel phones with security improvements\n- AI Overviews are being integrated into Google Search\n- Android is being enhanced with Gemini Nano for better multimodal capabilities\n\n📈 Financial Performance (Q3 2024):\n- Revenue up 15% year-over-year to $88.3 billion\n- Google Services revenue increased 13% to $76.5 billion\n- Google Cloud revenue grew 35% to $11.4 billion\n- Operating margin expanded by 4.5 percentage points to 32%\n- Net income and EPS both increased by 34%\n\n🌐 Market Position:\n- Maintains over 90% global search market share\n- 88% market share in the United States\n- Processes approximately 6.3 million searches per minute\n- Continues to lead in web discovery despite emerging AI-powered alternatives\n\nThe company appears to be strongly focused on AI integration across its products and services, while maintaining robust financial growth and market dominance."
          },
          "name": "print_output",
          "type": "tool_use"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01HyGb3KNm4XhuGMDHSwD7S6",
          "content": "{\"answer\":\"Here are the key recent developments about Google:\\n\\n🔍 Recent News & Developments:\\n- Google has launched Gemini 2.0 and a new quantum computing chip called Willow\\n- Google TV is getting new AI features powered by Gemini\\n- The company released a January 2025 update for Pixel phones with security improvements\\n- AI Overviews are being integrated into Google Search\\n- Android is being enhanced with Gemini Nano for better multimodal capabilities\\n\\n📈 Financial Performance (Q3 2024):\\n- Revenue up 15% year-over-year to $88.3 billion\\n- Google Services revenue increased 13% to $76.5 billion\\n- Google Cloud revenue grew 35% to $11.4 billion\\n- Operating margin expanded by 4.5 percentage points to 32%\\n- Net income and EPS both increased by 34%\\n\\n🌐 Market Position:\\n- Maintains over 90% global search market share\\n- 88% market share in the United States\\n- Processes approximately 6.3 million searches per minute\\n- Continues to lead in web discovery despite emerging AI-powered alternatives\\n\\nThe company appears to be strongly focused on AI integration across its products and services, while maintaining robust financial growth and market dominance.\"}"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "text": "Okay, let me use the research agent to gather some recent news about Google:",
          "type": "text"
        },
        {
          "id": "toolu_01K1fwpyy3nzxZc7DvPT3nC8",
          "input": {
            "question": "recent news about Google"
          },
          "name": "research_agent",
          "type": "tool_use"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01K1fwpyy3nzxZc7DvPT3nC8",
          "content": "{\"answer\":\"Here are the key recent developments about Google:\\n\\n🔍 Recent News & Developments:\\n- Google has launched Gemini 2.0 and a new quantum computing chip called Willow\\n- Google TV is getting new AI features powered by Gemini\\n- The company released a January 2025 update for Pixel phones with security improvements\\n- AI Overviews are being integrated into Google Search\\n- Android is being enhanced with Gemini Nano for better multimodal capabilities\\n\\n📈 Financial Performance (Q3 2024):\\n- Revenue up 15% year-over-year to $88.3 billion\\n- Google Services revenue increased 13% to $76.5 billion\\n- Google Cloud revenue grew 35% to $11.4 billion\\n- Operating margin expanded by 4.5 percentage points to 32%\\n- Net income and EPS both increased by 34%\\n\\n🌐 Market Position:\\n- Maintains over 90% global search market share\\n- 88% market share in the United States\\n- Processes approximately 6.3 million searches per minute\\n- Continues to lead in web discovery despite emerging AI-powered alternatives\\n\\nThe company appears to be strongly focused on AI integration across its products and services, while maintaining robust financial growth and market dominance.\"}"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "text": "The research agent has provided a comprehensive summary of the recent news and developments around Google. This covers their financial performance, market position, and key product updates like Gemini and Pixel. I believe this information answers the original request well.",
          "type": "text"
        }
      ]
    }
  ]

@app.route("/")
def get():
    return Titled("Agent UI",
        Container(
            H1("Message Flow", cls="text-2xl font-bold mb-6"),
            Div(
                *[ChatMessage(msg) for msg in messages],
                cls="max-w-4xl mx-auto space-y-2"
            )
        )
    )

serve()