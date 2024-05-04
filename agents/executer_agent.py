import json
from llmclient import generate_response_executer
from functions import get_functions_dict, get_openai_functions_definitions
import streamlit as st
import re
from time import sleep
from pathlib import Path
import base64



# create function that creates a client with instructor


system_prompt = f"""You are a helpful assistant.
You can use the following actions:

{str(get_openai_functions_definitions())}

Acomplish the task in steps. If you get error in previous step fix it in the current step. Use the following format:

Step 1: The action in the JSON plan
Plan: Your plan for this step and the next step
Action: the action to take, should be one of ['historicalprice-tool', 'line-chart-tool', 'None'].
Input: the input to the action, should be a valid JSON object
Observation: the result of the action

Step 2: The action in the JSON plan
Plan: Your plan for this step and the next step
Action: the action to take, should be one of ['historicalprice-tool', 'line-chart-tool', 'None'].
Input: the input to the action , should be a valid JSON object
Observation: the result of the action

... (this Step/Plan/Action/Input/Observation repeats for all steps)

Once you have completed all the steps, your final answer should be in the format:
Final Answer: the final answer to the user_request_summary

Begin! Reminder to use tools if necessary. When you want to respond directly, you can choose 'None' as the action. Your action input can be your answer to user. NEVER assume the user's input. 

"""



def remove_unnecessary_text(text):
    # Regular expression pattern for "Step X:"
    pattern = r"Step \d+:"

    # Use re.split() to split the string on the pattern
    parts = re.split(pattern, text)

    # The second part of the split is everything after "Step X:"
    text = parts[0]

    return text

def execute_function(function_name: str, function_args: str) -> str:
    print(f"Function name: {function_name}")
    if function_name != "none":
        try:
            function_to_call = get_functions_dict()[function_name].func
            function_args = json.loads(function_args)
            function_response = function_to_call(**function_args)
            print(f"Function response: {function_response}")
            return function_response
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return ""
    
def get_steps_size(data):
    json_data = json.loads(data)
    steps_size = len(json_data["steps"])
    return steps_size

def find_step_lines(text):
    lines = text.split('\n')
    pattern = re.compile(r"\s*Step (\d+): (.*)")
    matching_lines = [line for line in lines if pattern.match(line)]
    if not matching_lines:
        raise ValueError("No matching line found")
    return matching_lines[0].lstrip()

def replace_img_markdown(markdown):
    pattern = r'(!\[.*?\]\((.*?)\))'
    matches = re.findall(pattern, markdown)
    for match in matches:
        html_img = img_to_html(match[1])
        markdown = markdown.replace(match[0], html_img)
    return markdown

def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
      img_to_bytes(img_path)
    )
    return img_html

def run(content):
    tools = ["historicalprice-tool", "line-chart-tool", "none"]
    count = 0
    previous_step_number = 0
    expander = None
    isfinalanswer = False
    steps_size = get_steps_size(content)
    while(True):
        print("Previous step number: ", previous_step_number)
        count = count + 1
        if count > 9:
            raise ValueError("Too many steps")
        #print(Fore.BLUE + content)
        output = generate_response_executer(system_prompt,content)
        if "Final Answer:" in output:
            isfinalanswer = True
            output = remove_unnecessary_text(output)
        output = output.replace("\nObservation:", "")
        multilinestr = output.replace("\n", "\n\n")      
        regex = r"Action\s*\d*\s*:(.*?)\nInput\s*\d*\s*:[\s]*(.*)"
        step_number_match = re.search(r"\s*Step (\d+): (.*)", output)
        if step_number_match is not None:
            step_number = int(step_number_match.group(1))
            messages = []
            placeholder = st.empty()
            expander_text = find_step_lines(output)
            with placeholder.container():
                expander = st.expander(f"**{expander_text}**", expanded=True)
        if isfinalanswer:
            st.markdown(replace_img_markdown(output), unsafe_allow_html=True)
        else:    
            expander.write(multilinestr)
            messages.append(multilinestr)

        match = re.search(regex, output, re.DOTALL)

        if "Final Answer:" in output:
            break

        if  previous_step_number + 1 > steps_size:
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write("**Model forgot that there are no remaining steps**")
            output = "You have completed all of the steps. Please provide the final answer."
            content = content + "\n" + output
            continue

        if previous_step_number != 0 and step_number != previous_step_number + 1:
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write("**The model confused the task order**")
            output = "Please follow the task order. You are currently on step " + str(previous_step_number + 1) + "."
            content = content + "\n" + output
            continue

        """ if "Task" not in output:
            print(Fore.YELLOW + "The model didnt output a step.")
            output = "Please follow the format Task/Reason/Action/Input/Observation"
            content = content + "\n" + output
            continue """

        if "Plan" not in output:
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write("**The model didn't output a plan**")
            output = "Please follow the format Step/Plan/Action/Input/Observation"
            content = content + "\n" + output
            continue

        if output.count("Input") > 1:
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write("**The model went crazy**")
            output = "Please go one step at a time."
            content = content + "\n" + output
            continue

        if not match:
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write("**The model was sidetracked**")
            output = "You are not following the format. Please follow the given format."
            content = content + "\n" + output
            continue

        action = match.group(1).strip().lower()
        if action not in tools:
            output = f"Invalid Action. Your action should be one of {tools}."           
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write(f"**The model forgot his tools {output}**") 
            content = content + "\n" + output
            continue
        

        action_input = match.group(2)
        observation = execute_function(action, action_input)
        expander.write(f"\nObservation: {str(observation)}")
        
        
        if str(observation).startswith("Error"):
            placeholder.empty()
            expander = st.expander(f"❌**{expander_text}**", expanded=False)
            expander.write("".join(messages))
            st.write(f"**The model got an error from the function. Error: {str(observation)}**")
            content = content + "\n" + str(observation)
            continue
        
        previous_step_number = step_number       
        messages.append(f"\nObservation: {str(observation)}")
        sleep(1)
        placeholder.empty()
        expander = st.expander(f"✅**{expander_text}**", expanded=False)
        expander.write("".join(messages))
        output = output + "\nObservation: " + str(observation)
        content = content + "\n" + output
    return {"match_found": False}


