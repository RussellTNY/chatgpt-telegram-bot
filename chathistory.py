import os
import tiktoken
import csv
import datetime
from config import DEBUG,logger

# management of  conversation history

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

def num_tokens_from_a_prompt(prompt:str) ->int :
    messages = [{"role": "user", "content": prompt}]
    n_tokens = num_tokens_from_messages(messages)
    return n_tokens

# 返回当前路径
def get_conv_file(user_id: int) ->str :
    file_name = os.getcwd() + f"/history/{str(user_id)}.csv"
    return file_name

# save user conversation 
# format as $timestamp,$role, $user name,$message
# role canbe "assistant" or "user", as same as openai
# do not save system message
def _save_message(user_id : int, role: str, name: str, tokens:int, message: str):
    timestamp = datetime.datetime.now()

    # Create CSV file with user ID as file name if it doesn't exist
    file_name = get_conv_file(user_id)
    fieldnames = ['timestamp', 'role', 'name', 'message','tokens']
    if not os.path.isfile(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True) # create directory if it doesn't exist
        with open(file_name, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    # Append user message and timestamp to CSV file
    with open(file_name, mode='a') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow({'timestamp': timestamp,
                         'role':role, 
                         'name':name,  
                         'message': message, 
                         'tokens':f'{tokens}'})

def load_message(user_id : int) ->list:
    # Read the last 20 rows of the CSV file with user_id as the file name
    file_name = get_conv_file(user_id)
    with open(file_name, mode='r') as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)[-10:]

    return rows

# save bunch of messages
def save_prompt_messages(user_id : int, name: str, tokens:int, messages):
    # 存储最新消息
    if not messages:
        return
    message = messages[-1]
    if DEBUG:
        print(message)
    role = message.get("role")
    content = message.get("content")
    _save_message(user_id,name, role, tokens, message=content)