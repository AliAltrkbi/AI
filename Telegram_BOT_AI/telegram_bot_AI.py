import random
import json
import pickle
import numpy as np
import regex as re
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
import telebot
from telebot import types
from pyowm.owm import OWM
from googletrans import Translator
import wikipedia
import webbrowser
from pytube import YouTube
import os

# إعداد نموذج الدردشة
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json', encoding='utf-8').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbotmodel.h5')

# إعداد مترجم Google Translate
translator = Translator()

# إعداد مفاتيح API
OWM_API_KEY = '5a38db36afbbae4aa06ddde8c4cc9d27'
TELEGRAM_API_KEY = 'your bot api from bot_father'

bot = telebot.TeleBot(TELEGRAM_API_KEY)
owm = OWM(OWM_API_KEY)
mgr = owm.weather_manager()

# دالة لتجهيز النص
def clean_up_sentence(sentence):
    pattern = re.compile(r'\b[\p{L}]+\b', re.UNICODE)
    sentence_words = pattern.findall(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# دالة لإنشاء حقيبة الكلمات
def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)

# دالة للتنبؤ
def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

# دالة للحصول على الردود
def get_response(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

# دالة للرد
def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = get_response(ints, intents)
    return res

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="Hello, Welcome to WeatherXYZ....")

@bot.message_handler(commands=['location'])
def request_location(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Share Location", request_location=True))
    bot.send_message(chat_id=message.chat.id, text="Mind sharing your location?", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    forecasts = get_forecasts(lat, lon)
    bot.send_message(chat_id=message.chat.id, text=forecasts)

@bot.message_handler(commands=['option'])
def option(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Translate", callback_data="translate"),
               types.InlineKeyboardButton("ترجم", callback_data="translate1"))
    markup.row(types.InlineKeyboardButton("ابحث عن", callback_data="web_search1"),
               types.InlineKeyboardButton("Web Search", callback_data="web_search"))
    markup.row(types.InlineKeyboardButton("Open YouTube", callback_data="youtube"),
               types.InlineKeyboardButton("Download Video", callback_data="download"))
    markup.row(types.InlineKeyboardButton("تعلم البرمجة", callback_data="learn_programming"),
               types.InlineKeyboardButton("chat with bot", callback_data="chat"))
    bot.send_message(chat_id=message.chat.id, text="Choose one option...", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["translate","translate1", "web_search","web_search1", "youtube", "download", "learn_programming", "chat"])
def handle_callback(call):
    if call.data == "translate":
        bot.send_message(chat_id=call.message.chat.id, text="Please send me the text you want to translate to Arabic prefixed with 'translate'.")
    elif call.data == "translate1":
        bot.send_message(chat_id=call.message.chat.id, text="'أرسل النص المراد ترجمته إلى اللغة الإنكليزية مسبوق بـ كلمة 'ترجم.")
    elif call.data == "web_search":
        bot.send_message(chat_id=call.message.chat.id, text="Please send me the query you want to search prefixed with 'search about'.")
    elif call.data == "web_search1":
        bot.send_message(chat_id=call.message.chat.id, text="' أرسل الاستعلام المراد البحث عنه مسبوق بـ عبارة'ابحث عن.")
    elif call.data == "youtube":
        youtube_link = "https://www.youtube.com"
        bot.send_message(chat_id=call.message.chat.id, text=f"Opening YouTube: {youtube_link}")
        webbrowser.open(youtube_link)
    elif call.data == "download":
        bot.send_message(chat_id=call.message.chat.id, text="Please send me the YouTube link prefixed with 'download' to download the video.")
    elif call.data == "learn_programming":
        programming_sites = """
        Here are some educational websites for learning programming:
        - [Codecademy](https://www.codecademy.com/)
        - [Coursera](https://www.coursera.org/)
        - [edX](https://www.edx.org/)
        - [Khan Academy](https://www.khanacademy.org/)
        - [Udacity](https://www.udacity.com/)
        - [Udemy](https://www.udemy.com/)
        """
        bot.send_message(chat_id=call.message.chat.id, text=programming_sites, disable_web_page_preview=True)
    elif call.data == "chat":
        bot.send_message(chat_id=call.message.chat.id, text="Please send your message to chat with the bot.")
    bot.answer_callback_query(callback_query_id=call.id)

@bot.message_handler(func=lambda message: 'translate' in message.text.lower())
def translate_message_handler(message):
    text_to_translate = message.text.replace('translate', '').strip()
    translation = translator.translate(text_to_translate, dest='ar')
    bot.reply_to(message, translation.text)

@bot.message_handler(func=lambda message: 'ترجم' in message.text.lower())
def translate_message_handler(message):
    text_to_translate = message.text.replace('ترجم', '').strip()
    translation = translator.translate(text_to_translate, dest='en')
    bot.reply_to(message, translation.text)

@bot.message_handler(func=lambda message: 'ابحث عن' in message.text.lower())
def search_message(message):
    query = message.text.replace('ابحث عن', '').strip()
    try:
        wikipedia.set_lang('ar')
        summary = wikipedia.summary(query)
        bot.send_message(chat_id=message.chat.id, text=summary)
    except wikipedia.exceptions.PageError:
        bot.send_message(chat_id=message.chat.id, text="لم يتم العثور على نتائج للبحث.")
    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        options_text = "\n- ".join(options)
        bot.send_message(chat_id=message.chat.id, text=f"الرجاء تحديد الاختيار المناسب:\n- {options_text}")

@bot.message_handler(func=lambda message: 'search about' in message.text.lower())
def search_message(message):
    query = message.text.replace('search about', '').strip()
    try:
        wikipedia.set_lang('en')
        summary = wikipedia.summary(query)
        bot.send_message(chat_id=message.chat.id, text=summary)
    except wikipedia.exceptions.PageError:
        bot.send_message(chat_id=message.chat.id, text="No results found.")
    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        options_text = "\n- ".join(options)
        bot.send_message(chat_id=message.chat.id, text=f"Please specify one of the following options:\n- {options_text}")

@bot.message_handler(func=lambda message: 'download' in message.text.lower())
def play_video(message):
    video_url = message.text.replace('download', '').strip()
    if not video_url.startswith('http'):
        bot.reply_to(message, "Please provide a valid YouTube link.")
        return
    try:
        yt = YouTube(video_url)
        video_title = yt.title
        video_stream = yt.streams.get_highest_resolution()

        video_path = video_stream.download()

        bot.send_video(message.chat.id, video=open(video_path, 'rb'), caption=video_title)

        os.remove(video_path)
    except Exception as e:
        bot.reply_to(message, f"Error downloading video: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo(message):
    if not(any(keyword in message.text.lower() for keyword in ['translate', 'search about', 'download', 'ترجم', 'ابحث عن'])):
        response = chatbot_response(message.text)
        bot.send_message(chat_id=message.chat.id, text=response)
    else:
        bot.send_message(chat_id=message.chat.id, text=message.text.upper())

def get_forecasts(lat, lon):
    observation = mgr.forecast_at_coords(lat, lon, '3h')
    forecasts = observation.forecast

    results = []

    for forecast in forecasts:
        time = forecast.reference_time('iso')
        status = forecast.status
        detailed = forecast.detailed_status
        temperature = forecast.temperature('celsius')
        temp = temperature['temp']
        temp_min = temperature['temp_min']
        temp_max = temperature['temp_max']

        results.append(f"""
        Location : Latitude {lat}, Longitude {lon}
        Time : {time}
        Status : {status}
        Detailed : {detailed}
        Temperature : {temp}°C
        Min Temperature : {temp_min}°C
        Max Temperature : {temp_max}°C
        """)

    return "\n".join(results[:1])

if __name__ == "__main__":
    bot.polling()
