import openai
import tiktoken
from config import CHAT_MODEL, COMPLETIONS_MODEL , SYS_MESSAGE_CAMPBELL, MAX_INPUT_TOKENS,MAX_CONVERSATIONS, GPT_ERROR, DEBUG, logger
from chathistory import num_tokens_from_messages, save_prompt_messages
import os

openai.api_key = os.environ.get("OPENAI_API_KEY", "default-api-key")

# define message for convenient use
class Message:
    
    def __init__(self, role,content):
        self.role = role
        self.content = content
        
    def message(self):
        return {
            "role": self.role,
            "content": self.content
        }

#management of  conversation with gpt
class AskGPT:
     
    def __init__(self, user_id:int, user_name: str):
        self.id = user_id
        self.name = user_name
        self.conversation_history = []  
        self.cur_tokens = 0

    #def __del__(self):
    #    self._save_conversation()

    def _adjust_sys_msg_with_prompt(self, prompt: str) -> str:
        num_words = 0
        if len(prompt.split()) < 15:
            num_words = 30
        elif len(prompt.split()) < 30:
            num_words =  50
        elif len(prompt.split()) > 300:
            num_words = 300
        else:
            num_words =  int(1.5 * len(prompt.split()))
        sys_msg = SYS_MESSAGE_CAMPBELL.replace("no more than 30 words", 
                                               f"no more than {num_words} words")
        return sys_msg

    # generate the minimum prompt message
    def _gen_prompt_simple(self, user_message:str) ->list:
        messages = []
        message = Message("system", self._adjust_sys_msg_with_prompt(user_message))
        messages.append(message.message())
        message = Message("user", user_message)
        messages.append(message.message())
        return messages

    # generate prompt messages with conversation history
    def _gen_prompt_using_history(self, prompt:str, max_response_tokens=300) ->list:
        
        messages = []
        [messages.append(msg) for msg in self.conversation_history]
        #messages = self.conversation_history.copy()
        messages.insert(
            -1,
            {
                "role": 'system',
                "content": self._adjust_sys_msg_with_prompt(prompt)
                }
        )
        #resolve token limits
        prompt_max_tokens = MAX_INPUT_TOKENS - max_response_tokens

        token_count = num_tokens_from_messages(messages)
        if DEBUG:
            print(f"{self.name} :{prompt} \nToken count: {token_count}")
            logger.info(f"{self.name} :{prompt} \nToken count: {token_count}")

        # remove first message while over the token limit
        while token_count > prompt_max_tokens:
            messages.pop(0)
            token_count = num_tokens_from_messages(messages)
        return messages    
    
    # save conversation locally
    def _save_conversation(self, message):
         # add user message
        self.conversation_history.append(message)
        save_prompt_messages(self.id, self.name, self.cur_tokens, messages=self.conversation_history)
        #manage the conversation length
        if len(self.conversation_history) < MAX_CONVERSATIONS:
            return
        else:
            self.conversation_history.pop(0)
    
    # internal func using openai, input: messages, output: assistant content
    def _send_message_to_gpt(self, messages):
        try:
            response = openai.ChatCompletion.create(
              model=CHAT_MODEL,
              messages=messages,
              temperature=0.7
            )
            
            self.cur_tokens = response["usage"]["total_tokens"]
            response_message = Message(
                response['choices'][0]['message']['role'],
                response['choices'][0]['message']['content']
            )
            return response_message.message()
            
        except Exception as e:
            return {"role":GPT_ERROR,
                    "content":f"Request failed with exception {e}"}  

    #   to send and receive message from gpt without conversation history
    def get_response_simple(self, prompt:str) ->str:
        self._save_conversation(Message("user", prompt).message())
        messages = self._gen_prompt_simple(prompt)
        response = self._send_message_to_gpt(messages)

        if response.get("role") == GPT_ERROR:
            print(f"{GPT_ERROR}:{response.get('content')}")
            return GPT_ERROR
        #add assistant reply
        self._save_conversation(response)
        if DEBUG:
            logger.info(f"Campbell :{response} \nReal token usage: {self.cur_tokens}")
            print(f"Campbell :{response} \nReal token usage: {self.cur_tokens}")

        return response.get("content")
        
    #  
    def get_response(self, prompt:str) ->str:
        #[self.conversation_history.append(x) for x in messages]
        self._save_conversation(Message("user", prompt).message())

        messages = self._gen_prompt_using_history(prompt)
        if DEBUG:
            logger.info(f"SEND:{messages}")
            print(f"SEND:{messages}")
        assistant_response = self._send_message_to_gpt(messages)     
        if DEBUG:
            logger.info(f"RECEIVE:{assistant_response}") 
            print(f"RECEIVE:{assistant_response}") 
        if assistant_response.get("role") == GPT_ERROR:
            #打印错误信息
            logger.error(f"{GPT_ERROR}:{assistant_response.get('content')}")
            return GPT_ERROR
        #clear the temp message
        messages.clear()
        #del messages[:] 
        self._save_conversation(assistant_response)
        if DEBUG:
            logger.info(f"Campbell :{assistant_response} \nReal token usage: {self.cur_tokens}")
            print(f"Campbell :{assistant_response} \nReal token usage: {self.cur_tokens}")

        return assistant_response.get("content")
