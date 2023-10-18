from nltk.corpus import wordnet
from SynonymsReplacer import SynonymsReplacer
from TransError import TransError
from Translation import Translation
import time
import argparse
import re
from LAC import LAC
import jieba

pattern = re.compile(r"[A-Z]")
stop_words = []
city_names = []
people_names = []
T_DIS = 0
lac = LAC(mode='lac')

def read_stop_words():
    global stop_words
    f = open('./tools/stop_words.txt', mode='r')
    line = f.readline()
    while line:
        line = line[:-1]
        stop_words.append(line)
        line = f.readline()

def load_china_city():
    global city_names
    f = open('./tools/china_city.txt', mode='r')
    line = f.readline()
    while line:
        line = line[:-1]
        city_names.append(line)
        line = f.readline()

def load_china_name():
    global people_names
    f = open('./tools/china_people.txt', mode='r')
    line = f.readline()
    while line:
        line = line[:-1]
        people_names.append(line)
        line = f.readline()

def load_trans_sent(file_name):
    test_list = []
    f = open(file_name, mode='r')
    line = f.readline()
    sent_list = []
    while line:
        if "sent_id" in line:
            print(line)
            line = f.readline()
            group_list = []
            step_list = []
            group_list.append(line[:-1])
            line = f.readline()
            step_list.append(group_list)
            sent_list.append(step_list)
        elif "add [" in line:
            print(line)
            line = f.readline()
            print(line)
            step_list = []
            while ("add [" not in line) & ("FIN" not in line):
                group_list = []
                while line != "\n":
                    group_list.append(line[:-1])
                    line = f.readline()
                    print(line)
                step_list.append(group_list)
                print(len(step_list), "group finish")
                line = f.readline()
            sent_list.append(step_list)
            print(sent_list)
        elif "FIN" in line:
            test_list.append(sent_list)
            sent_list = []
            line = f.readline()
        else:
            line = f.readline()
    return test_list


def get_word_bag(word_list):
    word_bag = {}
    for word in word_list:
        if word in stop_words:
            continue
        if word in word_bag.keys():
            word_bag[word] += 1
        else:
            word_bag[word] = 0
            word_bag[word] += 1
    return word_bag


def cau_bow_distance(s_p, l_p):
    s_bow = get_word_bag(s_p)
    l_bow = get_word_bag(l_p)
    dis = 0
    error_word = []
    for key in s_bow.keys():
        if key in l_bow.keys():
            if s_bow[key] > l_bow[key]:
                dis += s_bow[key] - l_bow[key]
                error_word.append(key)
        else:
            dis += s_bow[key]
            error_word.append(key)
    print(dis, error_word)
    return dis, error_word


def get_nltk_sym(word):
    syn = set()
    wordnet.synsets(word, lang='cmn')
    for each in wordnet.synsets(word, lang='cmn'):
        list = each.lemma_names('cmn')
        for w in list:
            syn.add(w)
    return syn


def del_all_syn_word(error_word):
    words = jieba.cut_for_search(error_word)
    replacer = SynonymsReplacer(synonyms_file_path='./tools/HIT-IRLab-Synonyms.txt',
                                cws_model_path='./tools/ltp-models/3.4.0/ltp_data_v3.4.0/cws.model')
    syn_words = set()
    for w in words:
        print(w)
        if w == "节日":
            continue
        syn = replacer.get_syno_sents_list(w)
        syn = list(set(syn).union(set(get_nltk_sym(w))))
        syn_words = set(syn).union(syn_words)
        syn_words.add(w)

    return list(syn_words)


def get_leave_path(tree):
    path_list = []
    leaves = tree.leaves()
    for i in range(0, len(leaves)):
        t = tree.leaf_treeposition(i)
        cur_tree = tree
        path = []
        for index in range(len(t)):
            if index != len(t) - 1:
                cur_tree = cur_tree[t[index]]
                path.append(cur_tree.label())
            else:
                path.append(leaves[i])
        path_list.append(path)
    print(path_list)
    return path_list


def cmp_leave_path(last_tree, next_tree):
    orgi_paths = get_leave_path(last_tree)
    aug_paths = get_leave_path(next_tree)
    fail_paths = []
    cur_idx = 0
    for i in range(len(orgi_paths)):
        search_nodes = orgi_paths[i]
        leaf = orgi_paths[i][-1]
        search_nodes.pop()
        last_idx = cur_idx
        match_result = True
        while cur_idx < len(aug_paths):
            cur_nodes = aug_paths[cur_idx]
            start = 0
            end = len(cur_nodes)
            for node in search_nodes:
                if node in cur_nodes[start:end]:
                    idx = cur_nodes.index(node, start, end)
                else:
                    match_result = False
                    break
                if idx != -1:
                    start = idx + 1
                else:
                    match_result = False
                    break
            if match_result:
                break
            else:
                cur_idx += 1
        if not match_result:
            fail_paths.append(leaf)
            cur_idx = last_idx
        else:
            cur_idx += 1
    if len(fail_paths) != 0:
        return False, fail_paths
    else:
        return True, fail_paths


def find_trans_bug(last, next):
    bow_result = cau_bow_distance(last.seg_list, next.seg_list)
    dis = bow_result[0]
    error_words = bow_result[1]
    if dis > T_DIS:
        new_errors = list(error_words)
        for err in error_words:
            if len(err) == 1:
                new_errors.remove(err)
                continue
            ner_flag = lac.run(err)[1][0]
            if ner_flag in ["q", "PER", "m"]:
                if (err not in people_names) & (err not in city_names):
                    new_errors.remove(err)
                continue
            syn = del_all_syn_word(err)
            inter_list = [val for val in syn if val in next.trans]
            if len(inter_list) != 0:
                new_errors.remove(err)
        if len(new_errors) != 0:
            path_result = cmp_leave_path(last.nlp_tree, next.nlp_tree)
            if not path_result[0]:
                struct_error = path_result[1]
                people_error = [val for val in new_errors if val in people_names]
                loc_error = [val for val in new_errors if val in city_names]
                errors = [val for val in struct_error if val in new_errors]
                errors += people_error + loc_error
                if len(errors) != 0:
                    return False, errors
                else:
                    return True, errors
            else:
                return True, new_errors
        return True, new_errors
    else:
        return True, bow_result[1]


def save_error_info(f, error):
    error_info = error.save_error()
    f.write(error_info[0] + "\n")
    f.write(error_info[1] + "\n")
    f.write(error_info[2] + "\n")
    f.write("\n")


def test_sent(test_file, bug_file, s_id, e_id):
    test_list = load_trans_sent(test_file)
    f = open(bug_file, mode="a")
    for p in range(s_id, e_id):
        sent_list = test_list[p]
        source_sent = sent_list[0][0][0]
        last = Translation(source_sent.split(";")[0], source_sent.split(";")[1])
        sent_list.remove(sent_list[0])
        f.write("sent_id = " + str(p) + "\n")
        f.write("add [0]" + "\n")
        for i in range(0, len(sent_list[0])):
            print(source_sent, " cmp ", sent_list[0][0][i])
            sent_trans = sent_list[0][0][i].split(";")
            now = Translation(sent_trans[0], sent_trans[1])
            result = find_trans_bug(last, now)
            if not result[0]:
                if len(result[1]) != 0:
                    errors = TransError(last, now, " ".join(result[1]))
                    save_error_info(f, errors)
        for i in range(0, len(sent_list) - 1):
            f.write("add [" + str(i + 1) + "]" + "\n")
            step_list = sent_list[i]
            inc = 0
            for j in range(0, len(step_list)):
                sents = step_list[j]
                for k in range(0, len(sents)):
                    last = Translation(sents[k].split(";")[0], sents[k].split(";")[1])
                    next_step = sent_list[i + 1][k + inc]
                    for sent in next_step:
                        print(sents[k], " cmp ", sent)
                        now = Translation(sent.split(";")[0], sent.split(";")[1])
                        result = find_trans_bug(last, now)
                        if not result[0]:
                            if len(result[1]) != 0:
                                errors = TransError(last, now, " ".join(result[1]))
                                find_trans_bug(last, now)
                                save_error_info(f, errors)

                inc += len(sents)
        f.write("\n")
    f.close()


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
                        default=50)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    file_name = args.file_name
    mt_sys = args.MTSys
    s_id = args.sid
    e_id = args.eid
    translation_file = './translations/' + file_name + "_" + mt_sys + '_translation.txt'
    bug_file = './bugs/' + file_name + "_" + mt_sys + '_bug.txt'
    start = time.perf_counter()
    read_stop_words()
    load_china_city()
    load_china_name()
    test_sent(translation_file, bug_file, s_id, e_id)
    end = time.perf_counter()
    print(' Detecing bus Running time: %s Seconds' % (end - start))

