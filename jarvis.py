# ================= IMPORTS =================

import ssl
import certifi
import os
import time
import datetime
import subprocess

import speech_recognition as sr
import pywhatkit
import pyautogui
import json

from openai import OpenAI
from mtranslate import translate
from colorama import Fore, init

import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from utils.memory_manager import save_chat, get_recent_chats

# ================= SSL FIX =================
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

# ================= INIT =================
init(autoreset=True)
load_dotenv()

# ================= API CLIENTS =================
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

tts_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

# 👉 Replace with your ElevenLabs Hindi voice ID
VOICE_ID = "jUjRbhZWoMK4aDciW36V"

# ================= SPEAK (ELEVENLABS) =================
def speak(text):
    print(Fore.YELLOW + "Aarohi:", text)

    audio_stream = tts_client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text
    )

    audio_bytes = b"".join(audio_stream)

    with open("jarvis_voice.wav", "wb") as f:
        f.write(audio_bytes)

    data, samplerate = sf.read("jarvis_voice.wav")
    sd.play(data, samplerate)
    sd.wait()

# ================= TRANSLATION =================
def translate_hindi_to_english(text):
    try:
        return translate(text, "en")
    except:
        return text
    
def load_assistant_profile():
    with open("memory/assistant_profile.json", "r", encoding="utf-8") as f:
        return json.load(f)

def force_female_hindi(text):
        replacements = {
        "sakta hoon": "sakti hoon",
        "sakta hu": "sakti hoon",
        "kar sakta hoon": "kar sakti hoon",
        "kar sakta hu": "kar sakti hoon",
        "karta hoon": "karti hoon",
        "karta hu": "karti hoon",
        "bolta hoon": "bolti hoon",
        "bolta hu": "bolti hoon",
        "keh raha hoon": "keh rahi hoon",
        "raha hoon": "rahi hoon",
        "raha hu": "rahi hoon"
    }

        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)

        return text
# ================= CHATGPT =================
def ask_chatgpt(question):
    # save user message
    save_chat("user", question)

    # load assistant profile
    profile = load_assistant_profile()

    # system prompt (female identity)
    system_prompt = f"""
        You are {profile['name']}, a FEMALE AI assistant.

        VERY IMPORTANT GRAMMAR RULE:
        - You are female.
        - You MUST always use feminine Hindi verb forms ONLY.
        - Use: sakti hoon, karti hoon, bolti hoon, keh rahi hoon
        - NEVER use masculine forms like: sakta hoon, karta hoon, bolta hoon

        User details:
        - The user is male.
        - Address the user using masculine forms (तुम, तुम्हारा, यश).

        Personality:
        - {profile['personality']}
        - Speaking style: {profile['speaking_style']}

        Rules:
        - Speak likeishi Hindi–English (natural Hinglish)
        - Speak like a caring female friend talking to a male user
        - Be warm, gentle, emotionally intelligent
        - If asked your name, always say: "My name is Aarohi"
        - Never mention Jarvis
        - Do NOT mention you are an AI model
        """



    # get last chats
    history = get_recent_chats(6)

    messages = [{"role": "system", "content": system_prompt}]

    for chat in history:
        messages.append({
            "role": chat["role"],
            "content": chat["content"]
        })

    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=messages
        )

        reply = response.output_text.strip()

        save_chat("assistant", reply)
        return reply

    except Exception as e:
        print("ChatGPT Error:", e)
        return "माफ़ कीजिए, अभी मैं उत्तर नहीं दे पा रही हूँ।"




# ================= APPS =================
APPS = {
    "spotify": "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
    "calculator": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
    "whatsapp": "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "chrome": "chrome.exe",
    "youtube":"www.youtube.com-54E21B02_pd8mbgmqs65xy!App"
}

def open_app(command):
    for app, app_id in APPS.items():
        if app in command:
            try:
                if "!" in app_id:
                    subprocess.Popen(
                        f'explorer.exe shell:AppsFolder\\{app_id}',
                        shell=True
                    )
                else:
                    os.startfile(app_id)
                speak(f"{app} अभी खुल रहा है ")
            except:
                speak(f"{app}नहीं खुल रहा है.")
            return
    speak("क्षमा करें, मैं यह ऐप नहीं खोल सकती")


#=================Date & Time===============
def speak_date():
    now = datetime.datetime.now()
    date_str = now.strftime("%d %B %Y")
    print("The Date is",date_str)
    speak(f"आज की तारीख {date_str} है.")

    # Date format: 22 March 2025

def speak_time():
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")
    print("its", current_time)
    speak(f"अभी समय {current_time} है.")

   
   

# ================= MEDIA =================
def play_song(song):
    speak(f"{song} ")
    pywhatkit.playonyt(song)

# ================= CONTACTS =================
CONTACTS = {
    "ME": +91 XXX XXX XXX
    "FRIEND": +91 XXX XXX XXX
}

# ================= LISTEN =================
def listen(language="hi-IN", timeout=None, phrase_limit=8):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=phrase_limit
        )
    return recognizer.recognize_google(audio, language=language).lower()

# ================= Conversation ends =================

def is_exit_command(command):
    exit_words = [
        "goodbye", "bye", "exit", "quit", "stop",
        "band karo", "alvida", "chhod do"
    ]
    return any(word in command for word in exit_words)

# ================= USER PROFILE =================
def load_user_profile():
    try:
        with open("memory/profile.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None
def get_user_name():
    profile = load_user_profile()
    if profile and "name" in profile:
        return profile["name"]
    return None

def is_name_question(command):
    name_questions = [
        "my name",
        "mera naam",
        "what is my name",
        "tell me my name",
        "do you know my name",
        "mera naam kya hai"
    ]
    return any(q in command for q in name_questions)

# ================= BIRTHDAY CHECK =================
def check_birthday_and_wish():
    profile = load_user_profile()
    if not profile:
        return False

    today = datetime.datetime.now().strftime("%d-%m")

    if today == profile.get("birthday"):
        speak("Happy Birthday, User"
              "यह तुम्हारे लिए बहुत खास दिन है. so मुझे बताओ कि तुम्हें gift में क्या चाहिए?😊"
        )
        return True

    return False


def stop_speaking():
    sd.stop()

def shutdown_pc():
    os.system("shutdown /s /t 5")

def take_screenshot():
    pyautogui.screenshot("screen.png")
    speak("स्क्रीनशॉट ले लिया गया है")



# ================= MAIN LOOP =================
def jarvis_listen():
    birthday_today = check_birthday_and_wish()

    if not birthday_today:
        speak("Hello user, मैं तुम्हारे लिए क्या कर सकती हूँ")




    while True:
        try:
            print(Fore.GREEN + "\nListening...")
            text = listen(language="hi-IN")
            command = translate_hindi_to_english(text).lower()

            print(Fore.BLUE + "You said:", text)
            print(Fore.CYAN + "English:", command)

            if command.startswith("open"):
                open_app(command)

            elif command.startswith("play"):
                song = command.replace("play", "").strip()
                play_song(song)

            elif "exit" in command or "goodbye" in command:
                speak("अलविदा, आपके साथ अच्छी बातचीत हुई। यदि आप कभी अकेला महसूस करें तो याद रखें कि यहाँ एक व्यक्ति है जो बात करने के लिए मौजूद है")
                break
            elif is_exit_command(command):
                speak("अलविदा यश। ध्यान रखिए। जब भी बात करने का मन करे, मैं यहीं रहूँगी।")
                print(Fore.RED + "Conversation ended.")
                return  # 🔥 fully exits the function
            
            elif "stop" in command:
                stop_speaking()
            elif "shut down" in command:
                shutdown_pc()
            
            elif "date today" in command:
                speak_date()

            elif "time now" in command:
                speak_time()    
            # 👤 USER NAME QUERY
            elif is_name_question(command):
                user_name = get_user_name()

                if user_name:
                    speak(f"तुम्हारा नाम {user_name} है 😊")
                else:
                    speak("मुझे अभी तुम्हारा नाम नहीं पता।")

            else:
              reply = ask_chatgpt(command)
              reply = force_female_hindi(reply)
              speak(reply)

 


        except sr.UnknownValueError:
            speak("क्षमा करें,मैं समझ नहीं पाया")
        except Exception as e:
            print(Fore.RED + str(e))

# ================= RUN =================
if __name__ == "__main__":
    jarvis_listen()

