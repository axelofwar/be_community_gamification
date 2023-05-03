import openai
import os
import yaml
import asyncio
from dotenv import load_dotenv
# import cv2
from IPython.display import Markdown, display
load_dotenv()

'''
Tools for interacting with the OpenAI API - contains functions for:
    - Setting up the OpenAI API key
    - Getting the response from the Chat GPT API
'''

# LOAD PARAMETERS
with open("utils/yamls/params.yml", "r") as paramFile:
    params = yaml.load(paramFile, Loader=yaml.FullLoader)


# POPULATE OPENAI PARAMETERS
openai.api_endpoint = params["openai_endpoint"]+"/chat/completions"
print("OpenAI API Endpoint: ", openai.api_endpoint)

openai.api_key = os.environ['OPENAI_API_KEY']
if not openai.api_key:
    openai.api_key = ""
    print("OPENAI API KEY NOT FOUND")


# CHAT GPT REPONSE CALL
async def chatGPTcall(mPrompt, mModel, mTemp, mTokens):  # function for ChatGPT call
    response = openai.Completion.create(
        model=mModel,
        prompt=mPrompt,
        # uniqueness modifiers
        temperature=mTemp,
        max_tokens=mTokens,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"])
    return response


# def ask_GPT4(system_intel, prompt, model):
#     result = openai.ChatCompletion.create(model=model,
#                                           messages=[{"role": "system", "content": system_intel},
#                                                     {"role": "user", "content": prompt}])
#     display(Markdown(result['choices'][0]['message']['content']))
#     return result['choices'][0]['message']['content']

# def gpt4_call(prompt, model="gpt-4-32k", max_tokens=5000, temperature=0.8, n=1):
#     response = openai.Completion.create(
#         engine=model,
#         prompt=prompt,
#         max_tokens=max_tokens,
#         temperature=temperature,
#         n=n,
#     )
#     return response.choices[0].text.strip()


# async def main():
#     # image = cv2.imread("outputs/Frame_103_2.jpg")
#     # print("Models: ", openai.Engine.list())
#     with open("outputs/fe.txt", "r") as promptFile:
#         fe_txt = promptFile.read()
#         promptFile.close()
#     # model = "code-davinci-002"
#     prompt = f"modify thie code below to solve the error, show only the completed modified output and no step by step instructions: {fe_txt}"
#     # response = await chatGPTcall(prompt, model, params["temp"], 5000)

#     # # print(response.choices[0].text)
#     # with open("outputs/chatGPT_response.txt", "w+") as chatGPTFile:
#     #     chatGPTFile.write(response.choices[0].text)
#     #     chatGPTFile.close()

#     system_intel = "You are GPT-4, answer my question as as a software developer and generate or modify the code appropriately. Assume that I know \
#     #     some basics about coding, and know a lot about python, but less about javascript and react."
#     # Call the function above
#     # model = "gpt-4-32k" "gpt-3.5-turbo-0301"
#     gpt4_response = ask_GPT4(system_intel, prompt, 'gpt-3.5-turbo-0301')
#     # gpt4_response = gpt4_call(prompt, model="gpt-4",
#     #                           max_tokens=5000, temperature=0.8, n=1)
#     with open("outputs/gpt4_response.txt", "w+") as gpt4File:
#         gpt4File.write(gpt4_response)
#         gpt4File.close()

# asyncio.run(main())
