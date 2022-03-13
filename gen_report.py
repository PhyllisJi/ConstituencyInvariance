import argparse
import random
import re
import string
import time

import jieba
import xlsxwriter
from stanfordcorenlp import StanfordCoreNLP
from Bug import Bug
from nltk.corpus import wordnet

pattern = re.compile(r"[A-Z]")


def load_bug_info(file_name):
    f = open(file_name, mode="r")
    line = f.readline()
    bug_info = {}
    sent_bug = set()
    sent_id = -1
    while line:
        if "sent_id" in line:
            if sent_id != -1:
                bug_info[sent_id] = sent_bug
            sent_id += 1
            sent_bug = set()
        elif "add [" in line:
            pattern_num = re.compile(r"\d")
            idx = re.findall(pattern_num, line)[0]
        elif line != "\n":
            last_step = line[:-1]
            line = f.readline()
            next_step = line[:-1]
            error_words = f.readline()[:-1].split(" ")
            for w in error_words:
                if w in string.punctuation:
                    error_words.remove(w)
            bug = Bug(last_step, next_step, error_words, idx)
            sent_bug.add(bug)
        line = f.readline()
    bug_info[sent_id] = list(sent_bug)
    return bug_info


def random_without_same(low, high, num):
    s = []
    while len(s) < num:
        x = random.randint(low, high)
        if x not in s:
            s.append(x)
    return s



def group_name_bug(bug_info):
    bug_list = []
    for i in range(len(bug_info)):
        sent_bug = list(bug_info[i])
        bug_dict = {}
        for j in range(len(sent_bug)):
            bug = sent_bug[j]
            key = " ".join(bug.error_words)
            if key in bug_dict.keys():
                bug_dict[key].append(bug)
            else:
                bug_dict[key] = []
                bug_dict[key].append(bug)
        bug_list.append(bug_dict)
    return bug_list


def save_bug(bug_list, file_name):
    f = open(file_name, mode="w")
    for i in range(len(bug_list)):
        f.write("sent_id = " + str(i) + "\n")
        bug_dic = bug_list[i]
        count = 0
        for key in bug_dic.keys():
            f.write(str(count) + " " + key + "\n")
            for j in range(len(bug_dic[key])):
                bug = bug_dic[key][j]
                f.write(bug.last_step + "\n")
                f.write(bug.next_step + "\n")
                f.write(str(int(bug.step) - 1) + " -> " + str(bug.step) + "\n")
                f.write("\n")
            count += 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-name',
                        default='business_sent_1')
    parser.add_argument('--MTSys',
                        default='bing')
    return parser.parse_args()


def sample_bug(bug_info):
    bug_list = []
    for i in range(len(bug_info)):
        sent_bug = list(bug_info[i])
        bug_dict = {}
        idx = random_without_same(0, len(sent_bug)-1, len(sent_bug)/2)
        for j in idx:
            bug = sent_bug[j]
            key = " ".join(bug.error_words)
            if key in bug_dict.keys():
                bug_dict[key].append(bug)
            else:
                bug_dict[key] = []
                bug_dict[key].append(bug)
        bug_list.append(bug_dict)
    return bug_list


def write_results_in_excel(bug_file, xlsx_path, sheet_name):
    bug_info = load_bug_info(bug_file)
    bug_list = group_name_bug(bug_info)
    workbook = xlsxwriter.Workbook(xlsx_path)
    sheet = workbook.add_worksheet(sheet_name)
    value_title = [["sent_id", "error_word", "bug_id", "step", "original_sent", "translation"], ]
    index = len(value_title)
    for i in range(0, index):
        for j in range(0, len(value_title[i])):
            sheet.write(i, j, value_title[i][j])  # 像表格中写入数据（对应的行和列）
    bold_red = workbook.add_format({'bold': True,
                                    'font_color': 'red',
                                    'fg_color': '#7FFFAA', })
    merge_format_sentid = workbook.add_format({
        'bold': True,
        'border': 4,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#FFB6C1',
    })
    merge_format_bugid = workbook.add_format({
        'bold': True,
        'border': 4,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#B0C4DE',
    })
    merge_format_step = workbook.add_format({
        'bold': True,
        'border': 4,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#E1FFFF',
    })
    merge_format_error = workbook.add_format({
        'bold': True,
        'border': 4,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#FFE4E1',
    })
    rows_old = 1
    for sent_id in range(len(bug_list)):
        bug_id = 0
        bug_dic = bug_list[sent_id]
        if not bool(bug_dic):
            continue
        bug_count = 0
        start_row = rows_old
        for key in bug_dic.keys():
            idx = len(bug_dic[key])
            error_start = rows_old
            for j in range(0, idx):
                bug = bug_dic[key][j]
                print(bug.last_step)
                last_data = [sent_id, key, bug_id, str(int(bug.step) - 1) + " -> " + str(bug.step),
                             bug.last_step.split(";")[0], bug.last_step.split(";")[1]]
                next_data = [sent_id, key, bug_id, str(int(bug.step) - 1) + " -> " + str(bug.step),
                             bug.next_step.split(";")[0], bug.next_step.split(";")[1]]
                for c in range(len(last_data)):
                    if c == 5:
                        trans = last_data[c]
                        errors = key.split(" ")
                        args = (j * 2 + rows_old, c)
                        start = 0
                        for error in errors:
                            error_idx = trans.find(error, start)
                            if start != error_idx:
                                tmp_tup = (trans[start:error_idx], bold_red, error)
                            else:
                                tmp_tup = (bold_red, error)
                            args += tmp_tup
                            start = error_idx + len(error)
                        if trans[start:len(trans)] != '':
                            args += (trans[start:len(trans)],)
                        sheet.write_rich_string(*args)
                    else:
                        sheet.write(j * 2 + rows_old, c, last_data[c])
                    sheet.write(j * 2 + rows_old + 1, c, next_data[c])
                sheet.merge_range(j * 2 + rows_old, 2, j * 2 + rows_old + 1, 2, bug_id, merge_format_bugid)
                sheet.merge_range(j * 2 + rows_old, 3, j * 2 + rows_old + 1, 3,
                                  str(int(bug.step) - 1) + " -> " + str(bug.step), merge_format_step)
                bug_id += 1
            rows_old += idx * 2
            bug_count += idx
            sheet.merge_range(error_start, 1, rows_old - 1, 1, key, merge_format_error)
        sheet.merge_range(start_row, 0, rows_old - 1, 0, sent_id, merge_format_sentid)
    workbook.close()


def main():
    args = parse_args()
    file_name = args.file_name
    mt_sys = args.MTSys
    bug_file = './bugs/' + file_name + "_" + mt_sys + '_bug.txt'
    xlsx_file = './results/' + file_name + "_" + mt_sys + "_result.xlsx"
    start = time.perf_counter()
    write_results_in_excel(bug_file, xlsx_file, file_name + "_" + mt_sys + '_bug')
    end = time.perf_counter()
    print(end - start)



if __name__ == '__main__':
    main()

