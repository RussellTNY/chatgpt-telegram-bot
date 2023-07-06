import os
import azure.cognitiveservices.speech as speechsdk
from config import AUDIO_LANG_INPUT_EN, AUIDO_OUTPUT_EN,DEBUG, AUDIO_ERROR,AUDIO_SUCCESS,logger

# 配置语音识别服务
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), 
                                       region=os.environ.get('SPEECH_REGION'))

# speek using speaker from local device
def speak_out_local(text: str, voicetype:str = AUIDO_OUTPUT_EN):
    try:
        # 音频输出配置
        audio_output_config = speechsdk.audio.AudioOutputConfig(
            use_default_speaker=True)  # 用设备自带的speaker
        # The language of the voice that responds
        speech_config.speech_synthesis_voice_name = voicetype
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_output_config)

        # Azure text to speech output
        voice_result = speech_synthesizer.speak_text_async(text).get()

        # Check result
        if voice_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if DEBUG:
                print("Speech synthesized to speaker for text [{}]".format(text))
        elif voice_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = voice_result.cancellation_details
            print("Speech synthesis canceled: {}".format(
                cancellation_details.reason))
            logger.warning("Speech synthesis canceled: {}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error("Error details: {}".format(
                    cancellation_details.error_details))
    except Exception as ex:
        print(ex)
        logger.error(f"{ex}")
        return AUDIO_ERROR


# 语音生成到ogg文件, filename should be "xxx.ogg"
def gen_voice_file(text: str, filename: str, voicetype:str = AUIDO_OUTPUT_EN):
    try:
        # 音频输出配置
        speech_config.speech_synthesis_voice_name = voicetype
        # 设置输出语音的格式ogg
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus)

        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config) # audio config没有时语音输出到内存

        # 默认ogg语音文件写入路径
        voice_result = speech_synthesizer.speak_text_async(
            text=text).get()  # 语音合成

        # Check result
        if voice_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if DEBUG:
                print(f"Speech synthesized to file: {filename} for text [{text}]")
            # Write the audio to an OGG file, inside the current path
            with open(filename, "wb") as audio_file:
                audio_file.write(voice_result.audio_data)
            return AUDIO_SUCCESS
        elif voice_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = voice_result.cancellation_details
            logger.warning(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Error details: {cancellation_details.error_details}")
            return AUDIO_ERROR
    except Exception as ex:
        logger.error(f"{ex}")
        return AUDIO_ERROR


# 语音转文字,用设备自带的microphone
def text_from_local_mic(lang:str = AUDIO_LANG_INPUT_EN) ->str:
    try:
        # 音频输入配置
        audio_config = speechsdk.audio.AudioConfig(
            use_default_microphone=True)  # 用设备自带的mic
        # 被识别的语言设置
        speech_config.speech_recognition_language = lang
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config)
        
        # Get audio from the microphone and then send it to the TTS service.
        speech_recognition_result = speech_recognizer.recognize_once_async().get()

        # If speech is recognized, send it to Azure OpenAI and listen for the response.
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning(f"No speech could be recognized: {speech_recognition_result.no_match_details}")
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            logger.warning(f"Speech Recognition canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Error details: {cancellation_details.error_details}")
    except Exception as ex:
        print(ex)
        logger.error(f"{ex}")
    

# 从音频文件中识别文本, filename默认从当前文件夹中取
def text_from_file(filename:str, lang: str = AUDIO_LANG_INPUT_EN) ->str:
    try:
        speech_config.speech_recognition_language = lang
        audio_config = speechsdk.AudioConfig(filename=filename)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = speech_recognizer.recognize_once_async().get()
        return result.text
    except Exception as ex:
        print(ex)
        logger.error(f"{ex}")
