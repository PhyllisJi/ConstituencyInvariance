import argparse
import hashlib
import http
import json
import random
import re
import string
import sys
import time
import urllib
import uuid
from imp import reload

import pandas as pd
import requests
import ssl
import sys
import urllib.request as urllib2

reload(sys)
pattern_punc = re.compile(r"^ , | ,  , | ,  .+$")
pattern_mask = re.compile(r'\[\d\]')
pattern_char = re.compile(r"^[a-zA-Z0-9-,.]+$")
pattern_1 = re.compile(r" ,|, |,")
pattern_2 = re.compile(r" - ")
phrase_list = []
punc = string.punctuation


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    YOUDAO_URL = 'https://openapi.youdao.com/api'

    return requests.post(YOUDAO_URL, data=data, headers=headers, timeout=(3, 10))


def get_youdao_translation(sent):
    APP_KEY = ''
    APP_SECRET = ''
    data = {}
    data['from'] = 'en'
    data['to'] = 'zh-CHS'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(sent) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = sent
    data['salt'] = salt
    data['sign'] = sign
    response = do_request(data)
    contentType = response.headers['Content-Type']
    data = json.loads(response.content)
    if contentType == "audio/mp3":
        millis = int(round(time.time() * 1000))
        filePath = "合成的音频存储路径" + str(millis) + ".mp3"
        fo = open(filePath, 'wb')
        fo.write(response.content)
        fo.close()
    else:
        try:
            data = json.loads(response.content)
            return data['translation'][0]
        except:
            response = do_request(data)
   

def get_baidu_translation(q):
    appid = ''  
    secretKey = '' 
    httpClient = None
    myurl = '/api/trans/vip/translate'
    fromLang = 'auto'  
    toLang = 'zh'  
    salt = random.randint(32768, 65536)
    sign = appid + q + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign

    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com', timeout=10)
        httpClient.request('GET', myurl)
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        return result["trans_result"][0]['dst']
    except Exception as e:
        print(e)
    finally:
        if httpClient:
            httpClient.close()




def get_google_translation(q, lan):
    data = {}
    data["appkey"] = ""
    data["type"] = "google"
    data["from"] = "en"
    if "zh" in lan:
        data["to"] = "zh-CN"
    else:
        data["to"] = lan
    data["text"] = q
    url_values = urllib.parse.urlencode(data)
    url = "https://api.jisuapi.com/translate/translate" + "?" + url_values
    request = urllib2.Request(url)
    for i in range(5):
        try:
            result = urllib2.urlopen(request, timeout=10)
            jsonarr = json.loads(result.read())
            if jsonarr["status"] == 0:
                return jsonarr["result"]["result"]
                break
            else:
                print(jsonarr)
                if i < 5:
                    continue
        except:
            if i < 5:
                continue
            else:
                print('URLError: <urlopen error timed out> All times is failed ')


def get_bing_translation(source, lan):
    subscription_key = ""
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    path = '/translate'
    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': [lan]
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-type': 'application/json',
        'Ocp-Apim-Subscription-Region': 'eastasia'
        # 'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{
        'text': source
    }]
    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    return response[0]['translations'][0]['text']


def format_sent(sent):
    punc = [",", "\"", "\$", "\(", "\)", "\.","\:"]
    for p in punc:
        idx = re.finditer(p, sent)
        count = 0
        for i in idx:
            start = i.start()
            if sent[start + count - 1] != " ":
                sent = " ".join([sent[0:start + count], sent[start + count:len(sent)]])
                count += 1
            if start + count + 1 != len(sent):
                if sent[start + count + 1] != " ":
                    sent = " ".join([sent[0:start + count + 1], sent[start + count + 1:len(sent)]])
                    count += 1
    sent = re.sub(pattern_2, "-", sent)
    idx = sent.find("[")
    sent = sent[:idx] + " " + sent[idx:]
    idx = sent.find("]")
    sent = sent[:idx + 1] + " " + sent[idx + 1:]
    idx = sent.find("'s")
    sent = sent[:idx] + " " + sent[idx:]
    if idx == -1:
        idx = sent.find("'")
        sent = sent[:idx] + " " + sent[idx:]
        idx = sent.find("'")
        sent = sent[:idx + 1] + " " + sent[idx + 1:]
    sent = " ".join(sent.split())
    return sent


def format_abbr(sent):
    abbr = ["n't", "'s", "'re", "'ll", "'m"]
    words = sent.split(" ")
    for w in words:
        if w in abbr:
            idx = sent.find(w)
            sent = sent[:idx - 1] + sent[idx:]
    return sent


def sent_format(sent):
    p1 = re.compile(r" [!?',;]|[!?',;] | [!?',;]| \.$| \. $|\. $")
    p2 = re.compile(r"[!?',;.]")
    res = re.findall(p1, sent)
    res_idx = re.finditer(p1, sent)
    while len(res) != 0:
        diff_v = 0
        for r in res_idx:
            start = r.span()[0] - diff_v
            end = r.span()[1] - diff_v
            content = r.group()
            s_punc = re.findall(p2, r.group())[0]
            if s_punc == ".":
                if end == len(sent):
                    temp = len(sent)
                    sent = sent[:start] + "."
                    diff_v += temp - len(sent)
            else:
                temp = len(sent)
                sent = sent.replace(content, s_punc)
                diff_v += temp - len(sent)
        res_idx = re.finditer(p1, sent)
        res = re.findall(p1, sent)
    sent = sent.strip()
    sent = sent.rstrip()
    word = sent.split(" ")
    new_s = ""
    for w in word:
        if len(w) != 0:
            w = w.strip().rstrip()
            new_s += w + " "
    new_s = new_s[:-1]
    new_s = new_s.replace(",,", ',')
    new_s = new_s.replace("..", '.')
    new_s = new_s.replace(',.', '.')
    return new_s


def get_translation_by_sys(mt_sys, sent, lan):
    if 'baidu' in mt_sys:
        return get_baidu_translation(sent)
    if 'bing' in mt_sys:
        return get_bing_translation(sent, lan)
    if 'youdao' in mt_sys:
        return get_youdao_translation(sent)
    if 'google' in mt_sys:
        return get_google_translation(sent, lan)


def translate_sent(mt_sys, pred_file, trans_file, s_id, e_id, lan):
    f = open(pred_file, mode="r")
    w = open(trans_file, mode="a")
    line = f.readline()
    s_str = "sent_id = " + str(s_id)
    e_str = "sent_id = " + str(e_id)
    while s_str not in line:
        line = f.readline()
    while line:
        if e_str in line:
            break
        if "sent_id" in line:
            w.write(line)
        elif "add [" in line:
            w.write(line)
        elif line == "\n":
            w.write(line)
        elif "FIN" in line:
            w.write(line)
        else:
            sent = line[:-1]
            trans = get_translation_by_sys(mt_sys, sent, lan)
            print("{};{}".format(sent, trans))
            w.write("{};{}".format(sent, trans) + "\n")
        line = f.readline()
    f.close()
    w.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-name',
                        default='business_sent_1')
    parser.add_argument('--MTSys',
                        default='bing')
    parser.add_argument('--sid',
                        type=int,
                        default=0)
    parser.add_argument('--eid',
                        type=int,
                        default=10)
    parser.add_argument('--lan',
                        default="zh")
    return parser.parse_args()


def main():
    args = parse_args()
    file_name = args.file_name
    mt_sys = args.MTSys
    s_id = args.sid
    e_id = args.eid
    lan = args.lan
    print("translate param:" + file_name + " " + mt_sys)
    pred_file = './pred_sents/' + file_name + '_pred.txt'
    translation_file = './translations/' + file_name + "_" + mt_sys + '_translation' + '.txt'
    start = time.perf_counter()
    translate_sent(mt_sys, pred_file, translation_file, s_id, e_id, lan)
    end = time.perf_counter()
    print('Translating Sentences Running time: %s Seconds' % (end - start))



if __name__ == '__main__':
    main()

