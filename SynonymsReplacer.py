import re

from pyltp import Segmentor
import synonyms
import jieba

class SynonymsReplacer:
    def __init__(self, synonyms_file_path, cws_model_path):
        self.synonyms = self.load_synonyms(synonyms_file_path)
        self.segmentor = self.load_segmentor(cws_model_path)

    def __del__(self):
        """对象销毁时要释放pyltp分词模型"""
        self.segmentor.release()

    def load_segmentor(self, cws_model_path):
        """
        加载ltp分词模型
        :param cws_model_path: 分词模型路径
        :return: 分词器对象
        """
        segmentor = Segmentor()
        segmentor.load(cws_model_path)
        return segmentor

    def segment(self, sentence):
        """调用pyltp的分词方法将str类型的句子分词并以list形式返回"""
        result = self.segmentor.segment(sentence)
        return result

    def load_synonyms(self, file_path):
        """
        加载同义词表
        :param file_path: 同义词表路径
        :return: 同义词列表[[xx,xx],[xx,xx]...]
        """
        synonyms = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                synonyms.append(line.strip().split(' '))
        return synonyms

    def permutation(self, data):
        """
        排列函数
        :param data: 需要进行排列的数据，列表形式
        :return:
        """
        assert len(data) >= 1, "Length of data must greater than 0."
        if len(data) == 1:  # 当data中只剩（有）一个词及其同义词的列表时，程序返回
            return data[0]
        else:
            head = data[0]
            tail = data[1:]  # 不断切分到只剩一个词的同义词列表

        tail = self.permutation(tail)

        permt = []
        for h in head:  # 构建两个词列表的同义词组合
            for t in tail:
                if isinstance(t, str):  # 传入的整个data的最后一个元素是一个一维列表，其中每个元素为str
                    permt.extend([[h] + [t]])
                elif isinstance(t, list):
                    permt.extend([[h] + t])
        return permt

    def get_syno_sents_list(self, input_sentence):
        """
        产生同义句，并返回同义句列表，返回的同义句列表没有包含该句本身
        :param input_sentence: 需要制造同义句的原始句子
        :return:
        """
        assert len(input_sentence) > 0, "Length of sentence must greater than 0."
        seged_sentence = self.segment(input_sentence)

        candidate_synonym_list = []  # 每个元素为句子中每个词及其同义词构成的列表
        for word in seged_sentence:
            word_synonyms = [word]  # 初始化一个词的同义词列表
            for syn in self.synonyms:  # 遍历同义词表，syn为其中的一条
                if word in syn:  # 如果句子中的词在同义词表某一条目中，将该条目中它的同义词添加到该词的同义词列表中
                    # if syn[0][0].isalnum():
                    #     syn.remove(syn[0])
                    syn.remove(word)
                    word_synonyms.extend(syn)
            syn_yms = synonyms.nearby(word)[0]
            word_synonyms = list(set(word_synonyms).union(set(syn_yms)))
            candidate_synonym_list.append(word_synonyms)  # 添加一个词语的同义词列表

        perm_sent = self.permutation(candidate_synonym_list)  # 将候选同义词列表们排列组合产生同义句

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
