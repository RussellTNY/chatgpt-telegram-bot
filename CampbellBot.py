from telegram import Update
#from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
#from telegram import InlineQueryResultArticle, InputTextMessageContent
#from telegram.ext import InlineQueryHandler
from telegram.constants import ParseMode

import os
import openai
import azure.cognitiveservices.speech as speechsdk
from askgpt import AskGPT
from voice import gen_voice_file
from config import SYS_MESSAGE_CAMPBELL, CHAT_MODE, MODE_VOICE, MODE_TEXT,GPT_ERROR,DEBUG,AUDIO_ERROR,AUDIO_SUCCESS, logger

# manage user converation
conversations = []

# Defining a function to print out the conversation in a readable format
def print_conversation(messages):
    for message in messages:
        print(f"[{message['role'].upper()}]")
        print(message['content'])
        print()


# 定义start函数，用于回复/start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("%s: %s", user.first_name, update.message.text)
    # set the chat mode to be text
    context.user_data[CHAT_MODE] = MODE_TEXT
    await update.message.reply_text("Hello, "+ user.first_name+ ". How are you today?")

# /voice
async def voice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ""
    if CHAT_MODE not in context.user_data or context.user_data[CHAT_MODE] != MODE_VOICE:
        # as long as chat_mode is not voice, set it to voice mode
        context.user_data[CHAT_MODE] = MODE_VOICE
        message = "Copy that. Now voice mode is on."
    else :
        message = "You are using voice mode right now."
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message
        )


# /text
async def text_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ""
    if CHAT_MODE not in context.user_data or context.user_data[CHAT_MODE] != MODE_TEXT:
        context.user_data[CHAT_MODE] = MODE_TEXT        
        message = "Copy that. Going back to text mode. "    
    else:
        message = "You are using text mode right now."
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message
        )

# /deposit
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Payments are securely powered by Stripe. "
        )

# /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Your current balance is ${0.0}"
        )


# 不支持的command
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="That's not a valid command. You can check menu button down below for all available commands."
        )

async def gptanswer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # An example of a system message that primes the assistant to explain concepts in great depth
    MODEL = "gpt-3.5-turbo"
    user_content = update.message.text
    # get apikey
    #key = os.environ["OPENAI_API_KEY"]
    key = os.environ.get("OPENAI_API_KEY", "default-api-key")
    if key=="default-api-key":
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ask papa to solve the api key problem :)"
    )
        return 
    openai.api_key = key
    #{"role": "system", "content": "I want you to act as a spoken English teacher and improver. I will speak to you in English and you will reply to me in English to practice my spoken English. I want you to keep your reply neat, limiting the reply to 100 words. I want you to strictly correct my grammar mistakes, typos, and factual errors. I want you to ask me a question in your reply. Now let's start practicing, you could ask me a question first. Remember, I want you to strictly correct my grammar mistakes, typos, and factual errors."},
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYS_MESSAGE_CAMPBELL},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
    )

    print(response["choices"][0]["message"]["content"])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response["choices"][0]["message"]["content"]
    )


#feature 1: 区分不同的用户，每个用户有自己的context
#feature 2: 能够保存会话的context，用户能够继续上次的对话
#feature 3: 用户能够听到语音回复，支持英文
#feature 4: 用户能够用语音输入，支持中文，英文，日语，韩语，越南语，马来西亚语，泰国语，印尼语
async def ask_Campbell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_message = update.message.text
    if DEBUG:
        print("%s: %s", user.first_name, user_message)

    #每个user/session, create messages
    flag = 0
    response = GPT_ERROR
    if conversations:
        for conversation in conversations:
            if conversation.id == user.id:
                response = conversation.get_response(user_message)
                flag = 1
                break
    if not flag: #新用户
        logger.info("New user: %s", user.first_name)
        conversation = AskGPT(user.id, user.full_name)
        response = conversation.get_response(user_message)
    # response 生成失败
    if response == GPT_ERROR:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,text=response
        )
        return

    conversations.append(conversation)

    #logger.info("%s: %s", 'Campbell: ', response)
    if CHAT_MODE not in context.user_data:
        context.user_data[CHAT_MODE] = MODE_TEXT
    if context.user_data[CHAT_MODE] == MODE_TEXT:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,text=response
        )
    else: # 如果是voice mode，则生成语音回复
        #ogg 语音保存到当前文件夹内
        file = os.path.join(os.getcwd(), f'{user.id}.ogg')
        # 合成语音不成功
        if AUDIO_SUCCESS != gen_voice_file(response, file):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,text=GPT_ERROR)
            return
        else:
            await context.bot.send_voice(
            chat_id=update.effective_chat.id, voice=open(file=file, mode='rb'))
            if os.path.exists(file):
                os.remove(file) #删除文件
        #print_conversation(messages)

 
if __name__ == '__main__':
    #Campbell
    if DEBUG:
        #TBot
        print("TBot is on.")
        logger.info("TBot is on.")
        application = ApplicationBuilder().token('6167178675:AAHp_HjImMsYS3vvT9CCu1d9WRNomQfvdr0').build()
    else:
        #Ask Campbell
        logger.info("Campbell is on.")
        print("Campbell is on.")
        application = ApplicationBuilder().token('6128557543:AAGy7JB5y2yjrsVaSqN0_WTwdbxnzyfN-Pg').build()
    #TBot

    # /commands /start, /voice, /text, /deposit, /balance
    handlers = []
    start_handler = CommandHandler('start', start)  #生成’start‘ command的 handler
    voice_mode_handler = CommandHandler('voice',voice_mode)
    text_mode_handler = CommandHandler('text',text_mode)
    deposit_handler = CommandHandler('deposit', deposit)
    balance_handler = CommandHandler('balance', balance)
    # Other handlers
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    campbell_handler = MessageHandler(
        filters.TEXT &(~filters.COMMAND), 
        ask_Campbell
        #gptanswer
        ) #文本消息，用gpt回
    
    handlers.append(start_handler)
    handlers.append(voice_mode_handler)
    handlers.append(text_mode_handler)
    handlers.append(deposit_handler)
    handlers.append(balance_handler)
    handlers.append(unknown_handler)
    handlers.append(campbell_handler)
    application.add_handlers(handlers=handlers)

    # using polling to debug
    application.run_polling() #开始轮询
    
