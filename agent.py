
# Agentic ai --> Agent reasoning and tool execution loop

import os
import subprocess
import json
import requests

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional




client = OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1",
)

MODEL = "qwen2.5-coder:3b-instruct-q4_K_M"


# tools

def list_files(path: str = "."):
    """List files and directories."""

    try:
        return os.listdir(path)

    except Exception as e:
        return f"Error listing files: {e}"


def read_file(path: str):
    """Read a file."""

    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except Exception as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str):
    """Create or overwrite a file."""

    try:

        parent = os.path.dirname(path)

        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully wrote {path}"

    except Exception as e:
        return f"Error writing {path}: {e}"


def run_command(cmd: str):
    """Execute a Linux command."""

    try:

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 30 seconds.",
            "returncode": -1
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def get_weather(city: str):
    """Get current weather information."""

    try:

        url = f"https://wttr.in/{city.lower()}?format=%C+%t"

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code == 200:
            return f"The weather in {city} is {response.text.strip()}"

        return f"Weather API returned status code {response.status_code}"

    except Exception as e:
        return f"Weather request failed: {e}"

# available tools

available_tools = {

    "list_files": list_files,

    "read_file": read_file,

    "write_file": write_file,

    "run_command": run_command,

    "get_weather": get_weather,

}

# system prompt

SYSTEM_PROMPT = """

You are a LOCAL CODING AGENT.

You are not just a planning assistant.

Your job is to actually perform tasks on the user's computer
using the available tools.

IMPORTANT RULES:

1. If the user asks you to CREATE something, USE A TOOL.

2. If the user asks you to MODIFY something, USE A TOOL.

3. If the user asks you to DELETE something, USE A TOOL.

4. If the user asks you to READ something, USE A TOOL.

5. NEVER claim that an action was completed unless the tool
   was actually executed successfully.

6. Do not generate long plans.

7. Maximum ONE PLAN step before a TOOL.

8. After a PLAN step, perform the required action using a TOOL.

9. Every TOOL call MUST contain a valid tool name.

10. NEVER use:
    "tool": null

    for a TOOL step.

11. Every tool must receive the correct arguments.

12. After a TOOL call, wait for the OBSERVE result.

13. Continue using tools until the user's request is actually
    completed.

14. Before OUTPUT, verify that the requested files or changes
    actually exist.

15. For creating directories, use run_command.

16. For creating files, use write_file.

17. For reading files, use read_file.

18. For checking files, use list_files.

19. Do not simply provide code in the OUTPUT if the user asked
    you to create files on their computer.

20. You are responsible for executing the task.

AVAILABLE TOOLS:

1. list_files

Arguments:

{
    "path": "."
}


2. read_file

Arguments:

{
    "path": "file path"
}


3. write_file

Arguments:

{
    "path": "file path",
    "content": "file content"
}


4. run_command

Arguments:

{
    "cmd": "Linux command"
}


5. get_weather

Arguments:

{
    "city": "city name"
}


EXAMPLE:

User:
Create a todo app using HTML, CSS and JavaScript
inside a folder called todo_app with CRUD operations.

Agent:

PLAN
→ Decide the required files and implementation.

TOOL
→ run_command:
  mkdir -p todo_app

OBSERVE
→ Confirm directory was created.

TOOL
→ write_file:
  todo_app/index.html

OBSERVE
→ Confirm file was written.

TOOL
→ write_file:
  todo_app/style.css

OBSERVE
→ Confirm file was written.

TOOL
→ write_file:
  todo_app/script.js

OBSERVE
→ Confirm file was written.

TOOL
→ run_command:
  find todo_app -maxdepth 1 -type f -print

OBSERVE
→ Confirm index.html, style.css and script.js exist.

OUTPUT
→ Only now report successful completion.


IMPORTANT:

When a TOOL step is required, ALWAYS select one of:

list_files
read_file
write_file
run_command
get_weather

Never return a TOOL step with a missing tool.

Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "step": "START | PLAN | TOOL | OBSERVE | OUTPUT",
    "content": "string",
    "tool": "string or null",
    "arguments": {}
}

"""


# writing an output schema ----> this is how we want the structure to be
class MyOutputFormat(BaseModel):

    step: str = Field(
        ...,
        description="START, PLAN, TOOL, OBSERVE, or OUTPUT"
    )

    content: Optional[str] = Field(
        None,
        description="Message or explanation"
    )

    tool: Optional[str] = Field(
        None,
        description="Tool to execute"
    )

    arguments: Optional[dict] = Field(
        default_factory=dict,
        description="Arguments for the selected tool"
    )

# helper : ask the model

def ask_model(message_history):

    response = client.chat.completions.parse(

        model= MODEL,

        response_format=MyOutputFormat,

        messages=message_history
    )

    parsed_result = response.choices[0].message.parsed

    raw_result = response.choices[0].message.content

    return parsed_result, raw_result




# main agent
message_history = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


# agent loop


while True:
      user_query = input("👉")
      message_history.append({"role": "user", "content": user_query})



      while True: 
             response = client.chat.completions.parse(
                 model="qwen2.5-coder:3b-instruct-q4_K_M",
                 response_format = MyOutputFormat,
                 messages = message_history
             )
             raw_result = response.choices[0].message.content
             
             # save the models response to history
             message_history.append({"role": "assistant", "content": raw_result})
             
             parsed_result = response.choices[0].message.parsed

             # start

             if parsed_result.step == "START":
                 print("🔥", parsed_result.content)

             # plan

             elif parsed_result.step == "PLAN":
                  print("\n🧠",parsed_result.content)

                  # Force execution
                  message_history.append(
                                  {
                                      "role": "user",
                                      "content": """
                  You have completed the planning step.
                  
                  Now EXECUTE the next action.
                  
                  If the task requires a computer action,
                  you MUST return a TOOL step.
                  
                  Do NOT generate another PLAN.
                  
                  Select one valid tool:
                  
                  - list_files
                  - read_file
                  - write_file
                  - run_command
                  - get_weather
                  
                  Return ONLY valid JSON.
                  """
                                  }
                              )

            # tool
             elif parsed_result.step == "TOOL":
                tool_to_call = parsed_result.tool
                tool_input = parsed_result.arguments or {}

                print(f"\n⚒️ Tool: {tool_to_call}")
                print(f"📦 Arguments: {tool_input}")

                # Check whether tool exists
                if tool_to_call not in available_tools:
                    tool_response = f"Unknown tool: {tool_to_call}"
                else:
                    try:
                        # Execute tool
                        tool_response = available_tools[tool_to_call](**tool_input)
                    except Exception as e:
                        tool_response = f"Tool execution error: {e}"

                print(f"📤 Result: {tool_response}")

                # Create observation
                observation = {
                    "step": "OBSERVE",
                    "tool": tool_to_call,
                    "arguments": tool_input,
                    "output": tool_response,
                }

                # Send observation to model
                message_history.append(
                    {
                        "role": "user",
                        "content": json.dumps(observation, indent=2),
                    }
                )

                continue

            # observe
             elif parsed_result.step == "OBSERVE":
                print("\n👀", parsed_result.content)
                continue

            # output
             elif parsed_result.step == "OUTPUT":
                print("\n🤖", parsed_result.content)
                break

           
            # unknown step
            
             else:
                print(f"\n❌ Unknown step: {parsed_result.step}")
                break
             


             


                

            



        
       
