from groq import Groq


def createclient():
    client = Groq()
    return {"client" : client, "model": "llama3-70b-8192"}
    




def generate_response_llm(system_message, appended_messages, stop=None):
    messages = []
    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]

    messages.extend(appended_messages)
    print(messages)
    clientdict = createclient()
    
    client = clientdict["client"]
    model = clientdict["model"]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        stop=stop,
        temperature=0.2,
        max_tokens=1000
        )
    return resp

def generate_response_executer(system_message,user_input):
    messages = []
    system_message = {"role": "system", "content": system_message}
    messages.append(system_message)
    user_message = {"role": "user", "content": user_input}
    messages.append(user_message)
    clientdict = createclient()
    
    client = clientdict["client"]
    model = clientdict["model"]

    completion = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=0,
    stop=["Observation:"]
    )
    return completion.choices[0].message.content