
from ast import Not, Try, While
from pprint import pprint
from re import T
from unittest import skip
from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FlexSendMessage,FollowEvent,TemplateSendMessage,ButtonsTemplate
)
import json
import datetime

from flask_login import login_user, logout_user


app = Flask(__name__)

line_bot_api = LineBotApi('<   >')
handler = WebhookHandler('<   >')

json_open_person = open('person.json', 'r')
json_load_person = json.load(json_open_person)
json_open_user_status = open('user_status.json', 'r')
json_load_user_status = json.load(json_open_user_status)

def user_search(key):
    #search display name 
    for v in json_load_person.values():
        if v['user_name'] == key:
            return True
        
def user_id(key):
    #search display name 
    for v in json_load_user_status.keys():
        if v == key:
            return True

def user_status(key):
    if json_load_user_status[key]["status"] == "login":
        return True
        
def student_number_search(key):
    #search student number 4char
    for v in json_load_person.keys():
        if v == key:
            return True
        
def pass_recognition(key, passcode):
    #search passcode 6char
    if passcode == json_load_person[key]['key']:
        return True

@app.route("/")
def index():
    return render_template('/index.html')

@app.route("/Login")
def login():
    return 

@app.route("/Login/Home/")
def Home():
    return render_template('/home.html')

@app.route("/Login/Home/StudentCouncil")
def StudentCouncil():
    return render_template('/StudentCouncil.html')

@app.route("/Login/Home/StudentCouncil/OpinionBox")
def OpinionBox():
    with open("opinion.txt", mode='r', encoding="UTF-8") as f:
        l_strip = []
        for s in f.readlines():
            s.replace("\n","")
            l_strip.append(s)
        
        contents = '<h1 align="center">意見箱</h1>\n'
        for i in range(len(l_strip)):
            if i % 2 != 0:
                x = '<h4 style= "color : Blue">'+ l_strip[i] + "</h4>"
                contents = contents + "\n" + x
            else:
                x = '<p class="overflow-wrap-break-word">' + l_strip[i] + '</p>\n <hr width="1000" size="2" align="left" noshade="">'
                contents = contents + "\n" + x
        content = contents
        return render_template('/OpinionBox.html',content=content)



@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    name = profile.display_name
    id = profile.user_id
    #名前から探す->なければユーザー認証（１,4桁　２，パスワード6桁）->登録
    #search name
    if user_id(id) == True and user_status(id) == True:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("こんにちは、"+name+"さん。\nユーザー認証は終了しています。"))
    elif not id in json_load_user_status:
        json_load_user_status[id] = {"authentications":0,"status":"False","student_council_question": "False","grade":"0"}
        status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
        status_data = json.loads(status_data)
        with open("user_status.json", 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4, ensure_ascii=False)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("こんにちは、"+name+"さん。\nユーザー認証を行います。10回以内に認証できないと使用できなくなります。\n\n4桁の学籍番号と6桁のパスコードを入力してください。\n（例:410100212545）"))
    elif 0 <= json_load_user_status[id]["authentications"] < 10 :
        line_bot_api.reply_message(event.reply_token, TextSendMessage("こんにちは、"+name+"さん。\nユーザー認証を行います。あと" + str(10 - json_load_user_status[id]["authentications"]) + "回以内に認証できないと使用できなくなります。\n\n4桁の学籍番号と6桁のパスコードを入力してください。\n（例:410100212545）"))
    elif json_load_user_status[id]["authentications"] == 10 :
        line_bot_api.reply_message(event.reply_token, TextSendMessage("あなたは10回間違えました。担当者に報告してください。"))
        


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #logを送信
    dt_now = datetime.datetime.now()
    date_now = dt_now.strftime('%Y年%m月%d日 %H:%M:%S')
    profile = line_bot_api.get_profile(event.source.user_id)
    #log_id = "<  >"
    #line_bot_api.push_message(log_id, TextSendMessage(date_now + "\n" + "user_name:" + profile.display_name +"\n" + event.message.text))
    with open("log.txt", mode='a', encoding="UTF-8") as f:
        f.write('\n' + date_now + " user_name:" + profile.display_name +"\nmessage:" + event.message.text)
    name = profile.display_name
    id = profile.user_id
    question_id = "Cfbe8bf33b06c6cf0206b2e44691fccc9"
    
    
    #条件 ログインしていない（試行回数がないまたは、10回以下か）
    if json_load_user_status[id]["status"] == "False" and (json_load_user_status[id]["authentications"] == None or json_load_user_status[id]["authentications"] < 10):
        #受け取った10桁を分解して照合
        text = event.message.text
        student_number = text[0:4]
        student_passcode = text[4:10]
        if student_number_search(student_number) == True:
            if pass_recognition(student_number, student_passcode) == True:
                    #json書き込み
                    #person.jsonの書き込み
                    json_load_person[student_number]["user_name"] = name
                    json_load_person[student_number]["user_id"] = id
                    person_data = json.dumps(json_load_person, indent=4, ensure_ascii=False)
                    person_data = json.loads(person_data)
                    with open("person.json", 'w', encoding='utf-8') as f:
                        json.dump(person_data, f, indent=4, ensure_ascii=False)
                        
                    #user_status.jsonの書き込み
                    grade = student_number[0]
                    json_load_user_status[id]["authentications"] = 0
                    json_load_user_status[id]["status"] = "login"
                    json_load_user_status[id]["grade"] = grade
                    status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
                    status_data = json.loads(status_data)
                    with open("user_status.json", 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, indent=4, ensure_ascii=False)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage("ユーザー認証が完了しました。\nようこそ生徒会公式LINEへ。\n「メニュー」と送信するとメニューが出てきます。"))

            else:
                if json_load_user_status[id]["authentications"] == None:
                    json_load_user_status[id]["authentications"] = 1
                    status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
                    status_data = json.loads(status_data)
                    with open("user_status.json", 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, indent=4, ensure_ascii=False)
                else:
                    json_load_user_status[id]["authentications"] = json_load_user_status[id]["authentications"] + 1
                    status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
                    status_data = json.loads(status_data)
                    with open("user_status.json", 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, indent=4, ensure_ascii=False)
                line_bot_api.reply_message(event.reply_token, TextSendMessage("入力が間違っています。あと" + str(10 - json_load_user_status[id]["authentications"])) + "回間違えるとで使用できなくなります。\nもう一度入力してください。")
                
        else:
            if json_load_user_status[id]["authentications"] == None:
                json_load_user_status[id]["authentications"] = 1
                status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
                status_data = json.loads(status_data)
                with open("user_status.json", 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, indent=4, ensure_ascii=False)
            else:
                json_load_user_status[id]["authentications"] = json_load_user_status[id]["authentications"] + 1
                status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
                status_data = json.loads(status_data)
                with open("user_status.json", 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, indent=4, ensure_ascii=False)
                    
            line_bot_api.reply_message(event.reply_token, TextSendMessage("入力が間違っています。あと" + str(10 - json_load_user_status[id]["authentications"]) + "回間違えるとで使用できなくなります。\nもう一度入力してください。"))
    elif json_load_user_status[id]["authentications"] == 10:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("あなたは10回間違えました。担当者に報告してください。"))
    else:
        if event.message.text == "メニュー":
            flex_message_json_string="""
            {
            "type": "bubble",
            "direction": "ltr",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "メインメニュー",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#000000FF",
                    "align": "center",
                    "contents": []
                }
                ]
            },
            "hero": {
                "type": "image",
                "url": "https://lh3.googleusercontent.com/w7DcKxZZHdnSTd6Bi9ztA-B5PMTUeS9-LkgjP1ESsovjbBVaE4v-kJHrRqFvUgTidGux_92iSm3xLK3Lh1JKsud-zBS72ze9Zq9GZVUFtCuysTipRpYYrz0nlMZVXlR2O1c0RjwAhTfmpYvGzOzSvKXBZ4RkOo9p8XraYR1u-zBJoH9ALERimNuK__rzqEMa1TWgMCkczNayTcvJ-zNRYevcmd9GBPmy-nrbH80dTWaPKOJCGPF0W4f1avBeKD8b8anzZI83Ni1VFkgXxfr6wmuJ2DlHsON8o3J0NW2QY12v95Aix_i1ESmFpFUiID1K9nV9rZOx9ROYh9wo0QAVEqz94nzg8KxShabvA4-f3mCs1KIbsVIbIunH4Pkoydz4M51P_47uRc47RJ4s0IZ8jcDDlSTY9L3MvVspUHpTGH5hso7Jlf3EEFRVeJ4Ofm_tdJmuijnVJ-pTiI61IYYGvzG7WjB3vHb7rMoYZnsyVyrhprxjcsL58H_ZzYUeEo-sOCgxIX6UExaPE1AswYnZut1iMrylQ4Fl5ly5qav_Ig6dGvFa0TUvt4Qn78k6PA1WIg52oIfz9w-XxaNluxfVyffoCihlBoaELQ99wqWFY3it8tVfmQvupo_h1eMicxMg9UbSSUe_iFmw2qcOFoDRW2EgHUGtJtCPIhuh2qzZtMZ6r4e38WtAoS_wvfZLx0ap873wKlV97APPW1tAOx-lV1SV=w1032-h756-no?authuser=0",
                "gravity": "center",
                "size": "full",
                "aspectRatio": "1.51:1",
                "aspectMode": "fit",
                "action": {
                "type": "uri",
                "uri": "https://toyohashiminami-h.aichi-c.ed.jp/"
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "borderColor": "#FFFFFFFF",
                "contents": [
                {
                    "type": "text",
                    "text": "何をするか選択してね",
                    "align": "center",
                    "contents": []
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#CCFCF64C",
                "contents": [
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "意見箱",
                    "text": "生徒会へ意見"
                    }
                },
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "年間行事予定",
                    "text": "年間行事予定を教えて"
                    }
                }
                ]
            }
            }
            """
            
            flex_message_json_dict = json.loads(flex_message_json_string)
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text='メインメニュー', contents=flex_message_json_dict))
            
        elif event.message.text == "生徒会へ意見":
            json_load_user_status[id]["student_council_question"] = "True"
            status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
            status_data = json.loads(status_data)
            with open("user_status.json", 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=4, ensure_ascii=False)
            line_bot_api.reply_message(event.reply_token, TextSendMessage("意見等を入力してください。"))
                
        elif json_load_user_status[id]["student_council_question"] == "True":
            json_load_user_status[id]["student_council_question"] = "False"
            status_data = json.dumps(json_load_user_status, indent=4, ensure_ascii=False)
            status_data = json.loads(status_data)
            with open("user_status.json", 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=4, ensure_ascii=False)
            with open("opinion.txt", mode='a', encoding="UTF-8") as f:
                f.write('\n' + date_now + " grade:" + json_load_user_status[id]["grade"] +"\nopinion:" + event.message.text)
            #line_bot_api.push_message(question_id, TextSendMessage(date_now + "\n" + "user_name:" + profile.display_name +"\n" + event.message.text))
            line_bot_api.reply_message(event.reply_token, TextSendMessage("意見箱に\n" + event.message.text + "\nという内容を投函しました。"))
        elif event.message.text == "こんにちは" or event.message.text == "Hello" or event.message.text == "hello":
            line_bot_api.reply_message(event.reply_token, TextSendMessage(event.message.text))
        elif event.message.text == "円周率":
            line_bot_api.reply_message(event.reply_token, TextSendMessage("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564856692346034861045432664821339360726024914127372458700660631558817488152092096282925409171536436789259036001133053054882046652138414695194151160943305727036575959195309218611738193261179310511854807446237996274956735188575272489122793818301194912983367336244065664308602139494639522473719070217986094370277053921717629317675238467481846766940513200056812714526356082778577134275778960917363717872146844090122495343014654958537105079227968925892354201995611212902196086403441815981362977477130996051870721134999999837297804995105973173281609631859502445945534690830264252230825334468503526193118817101000313783875288658753320838142061717766914730359825349042875546873115956286388235378759375195778185778053217122・・・\nこの辺でやめておきましょう（＾ω＾）"))
        elif event.message.text == "年間行事予定を教えて":
            line_bot_api.reply_message(event.reply_token, TextSendMessage("４月　　入学式\n５月　　遠足（１・３年生）\n７月　　ジョブシャドウイング（２年生）\n　　　　夏季クラスマッチ\n９月　　南高祭（文化祭・体育大会）\n１０月　修学旅行（２年生）\n１１月　文化公演会\n１２月　高校生の仕事学（１年生）\n２月　　生活デザイン科卒業制作発表\n３月　　卒業証書授与式\n　　　　春季クラスマッチ"))

if __name__ == "__main__":
    app.debug=True
    app.run()