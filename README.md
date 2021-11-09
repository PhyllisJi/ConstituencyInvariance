# ConstituencyInvarianceTesting
## Python Version

- python 3.6

## Install Requested Python Packages

- jieba
- nltk
- LAC
- synonyms
- pyltp
- xlsxwriter
- stanfordcorenlp
- argparse

## Install models

- ltp-models 3.4.0
- Stanford Corenlp 
  - Chinese models

## Testing step
- Start Stanford Corenlp service(Linux/MacOS)
  - https://github.com/nltk/nltk/wiki/Stanford-CoreNLP-API-in-NLTK
- Translate sentences：
  - **python translate_sent.py --file-name XXXX --MTSys XXXX --sid X --eid X**
  - file-name: the file names in directory pred_sents
  - MTSys: bing; youdao; google; baidu
  - sid: the sentence id of starting translating
  - eid: the sentence id of ending translating
  
- Detect translation errors:
  - **python detect_bug.py --file-name XXXX --MTSys XXXX --sid X --eid X**
  - file-name: the file names in directory translations
  - MTSys: bing; youdao; google; baidu
  - sid: the sentence id of detecting errors
  - eid: the sentence id of detecting errors

- Generate error reports
  - **python gen_report.py --file-name XXXX --MTSys XXXX**
  - file-name: the file names in directory bugs
  - MTSys: bing; youdao; google; baidu

