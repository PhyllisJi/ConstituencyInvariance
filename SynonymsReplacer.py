import re

from pyltp import Segmentor
import synonyms
import jieba

class SynonymsReplacer:
    def __init__(self, synonyms_file_path, cws_model_path):
        self.synonyms = self.load_synonyms(synonyms_file_path)
        self.segmentor = self.load_segmentor(cws_model_path)

    def __del__(self):
        self.segmentor.release()

    def load_segmentor(self, cws_model_path):
        segmentor = Segmentor()
        segmentor.load(cws_model_path)
        return segmentor

    def segment(self, sentence):
        result = self.segmentor.segment(sentence)
        return result

    def load_synonyms(self, file_path):
        synonyms = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                synonyms.append(line.strip().split(' '))
        return synonyms

    def permutation(self, data):
        assert len(data) >= 1, "Length of data must greater than 0."
        if len(data) == 1:  
            return data[0]
        else:
            head = data[0]
            tail = data[1:] 

        tail = self.permutation(tail)

        permt = []
        for h in head:  
            for t in tail:
                if isinstance(t, str): 
                    permt.extend([[h] + [t]])
                elif isinstance(t, list):
                    permt.extend([[h] + t])
        return permt

    def get_syno_sents_list(self, input_sentence):
        assert len(input_sentence) > 0, "Length of sentence must greater than 0."
        seged_sentence = self.segment(input_sentence)

        candidate_synonym_list = []  
        for word in seged_sentence:
            word_synonyms = [word]  
            for syn in self.synonyms:  
                if word in syn: 
                    syn.remove(word)
                    word_synonyms.extend(syn)
            syn_yms = synonyms.nearby(word)[0]
            word_synonyms = list(set(word_synonyms).union(set(syn_yms)))
            candidate_synonym_list.append(word_synonyms) 

        perm_sent = self.permutation(candidate_synonym_list)  

        syno_sent_list = []
        my_re = re.compile(r'[A-Za-z]', re.S)

        for p in perm_sent:
            if isinstance(p, list):
                p = "".join(p)
            if p != input_sentence:
                res = re.findall(my_re, p)
                if len(res) == 0:
                    syno_sent_list.append(p)
        return syno_sent_list
