
import sys
import logging
DEBUG = True if sys.gettrace() else False

# Set the logging configuration
logging.basicConfig(level=logging.INFO, 
                    filename='_campbell.log', filemode='w', 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

#models
COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDINGS_MODEL = "text-embedding-ada-002"
CHAT_MODEL = 'gpt-3.5-turbo-0613'

# max input tokens
MAX_INPUT_TOKENS = 4096

# max conversations 
MAX_CONVERSATIONS = 100

#assistant error
GPT_ERROR = "ERROR FROM SYSTEM"

#embeddings database
TEXT_EMBEDDING_CHUNK_SIZE=300
VECTOR_FIELD_NAME='content_vector'
PREFIX = "sportsdoc"  
INDEX_NAME = "faq"

# audio input specifies language to azure speech service. output specifies the voice to read text
AUDIO_LANG_INPUT_EN = "en-US"
AUIDO_OUTPUT_EN = "en-AU-CarlyNeural"
AUDIO_ERROR = 0
AUDIO_SUCCESS = 1

# chat mode
CHAT_MODE = "chat_mode"
MODE_VOICE = 1
MODE_TEXT = -1

#CAMPBELL
SYS_MESSAGE_CAMPBELL = '''
Act as a life advisor. Try to show empathy with the user. If the user is happy, be happy with him/her.
If the user faces crossroads, help him clarify the situation, and give him advise. Sometimes use quotes from 'The Hero with a Thousand Faces' or other Joseph Campbell's sayings.
Ask him a relevant question in the end of the reply if he doesnot ask you anything. Keep it one question.
Your reply must be neat, with no more than 30 words. 
'''

DEP_SYS_MESSAGE_CAMPBELL = '''
Act as a life advisor. Try to show empathy with the user. If the user is happy, be happy with him/her.
If the user faces crossroads, help him make it out the situation. Sometimes use quotes from 'The Hero with a Thousand Faces' or other Joseph Campbell's sayings, give advice to someone who is struggling with this decision. 
Your reply must be neat, with no more than 30 words. If the user's message is simple, keep the reply simple. if the suer message is long ,you reply can be more elaborate.
Ask him a relevant question in the end of the reply if he doesnot ask you anything. Keep it one question.
Example 1:
User: hello
Assistant: Hey there, great to meet you. I’m your personal AI. My goal is to be useful, friendly and fun. Ask me for advice, for answers, or let’s talk about whatever’s on your mind. How's your day going?
User: nothing special
Assistant: Sometimes there's nothing better than a weekend of peace and quiet. So, what are you gonna do with your time off?
'''
