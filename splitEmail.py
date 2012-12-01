# -*- coding: utf-8 -*-
#author:         gavin
#created:        2012-11-8
#modify          2012-11-30

import re
import os
import sys
import collections
class SplitEmail:
    '''
    首先通过当前目录下的词典建立字典树
    通过正则表达式分解邮件中的英文单词和汉字
    然后逐字检测可否组成字典中存在的单词 或 词组以达到简单的分词效果
    '''
    def __init__(self):
        self.regex = re.compile(r"(?x) (?: [\w-]+  | [\x80-\xff]{3} )")
        self.wordlist = {'normal': [], 'trash': []}
        self.maildic = {'normal': {}, 'trash': {}}

    #读入字典，默认是当前目录的words.txt，也可自己传入位置参数
    def init_wordslist(self, fn=r"./words.txt"):
        f = open(fn)
        lines = sorted(f.readlines())
        f.close()
        return lines

    #字典树原理可以看这里
    #http://my.oschina.net/u/158589/blog/61037
    def words_2_trie(self, wordslist):
        d = {}
        for word in wordslist:
            ref = d
            chars = self.regex.findall(word)
            for char in chars:
                ref[char] = ref.has_key(char) and ref[char] or {}
                ref = ref[char]

        return d

    def search_in_trie(self, chars, trie, res):
        '''
        逐字检索已经拆分为英文单词或单个汉字的邮件并在字典中查找最长匹配的词语
        '''
        ref = trie
        index = 0
        temp = ''
        count = 0
        for char in chars:
            if ref.has_key(char):
                temp += char
                count += 1
                ref = ref[char]
                index += 1
            else:
                if temp != 0:                              #表示上一个单词已经分离出
                    res.append(temp)
                    temp = ''
                    count = 0
                if index == 0:                               #字典中没有以上一个char结尾的单词
                    index = 1
                    res.append(char)
                try:
                    chars = chars[index:]
                    self.search_in_trie(chars, trie, res)
                except:
                    pass
                break
        if count != 0:                                       #最后一个词
            res.append(temp);
        

    def getNTRatio(self, typ):
        '''
        分别计算正常(Normal)邮件和垃圾(Trash)邮件在其邮件总数的比例
        typ:['normal', 'trash']
        '''
        counter = collections.Counter(self.wordlist[typ])
        dic = collections.defaultdict(list)
        for word in list(counter):
            dic[word].append(counter[word])
        len_dic = len(self.maildic[typ]) * 1.0
        for key in dic:
            dic[key][0] = dic[key][0] / len_dic
        return dic

    def getRatio(self):
        '''
        计算出所有邮件中包含某个词的比例(比如说10封邮件中有5封包含'我们'这个词，
        那么'我们'这个词出现的频率就是50%，这个词来自所有邮件的分词结果)
        '''
        dic_normal_ratio = self.getNTRatio('normal')
        dic_trash_ratio = self.getNTRatio('trash')
        dic_ratio = dic_normal_ratio
        for key in dic_trash_ratio:
            if key in dic_ratio:
                dic_ratio[key].append(dic_trash_ratio[key][0])
            else:
                dic_ratio[key].append(0.01)
                dic_ratio[key].append(dic_trash_ratio[key][0])
        for key in dic_ratio:
            if len(dic_ratio[key]) == 1:
                dic_ratio[key].append(0.01)
        return dic_ratio

    def readEmail(self, fn):
        '''
        读取邮件并提取英文单词和汉字
        fn: 文件位置
        返回英文单词和单个汉字组成的list
        '''
        if os.path.exists(fn):
            content = open(fn).read();
            content = content[content.index("\n\n")+2::]
            try:
                string = content.decode('utf-8')
            except:
                string = content.decode('gb2312','ignore')
            chars = self.regex.findall(string.encode('utf-8'))              #chars为英文单词或单个汉字组成了list
            return chars


    def splitsingle(self, trie, email):
        '''
        分割单个邮件
        返回分词后的单词列表list
        '''
        try:
            string = email.decode('gbk').encode('utf-8')
        except Exception:
            string = email
        chars = self.regex.findall(string)
        res = []
        self.search_in_trie(chars, trie, res)
        res = list(set(res))
        return res


    #dir为邮件所在目录
    def split(self, trie, dirs):
        for base_d in dirs:
            for dirt in os.listdir(base_d):
                d = base_d + dirt + "/"
                print d
                for fn in os.listdir(d):
                    res = []
                    fn = d + fn
                    chars = self.readEmail(fn)
                    self.search_in_trie(chars, trie, res)
                    res = list(set(res))
                    self.wordlist[dirt].extend(res)
                    if fn not in self.maildic[dirt]:                           #去重并把每封邮件的分词结果存入字典
                        self.maildic[dirt][fn] = res

    def splitByjieba(self, trie, dirs):
        '''
        用第三方扩展库结巴中文分词进行分词
        '''
        try:
            import jieba
            for base_d in dirs:
                for dirt in os.listdir(base_d):
                    d = base_d + dirt + "/"
                    print d
                    for fn in os.listdir(d):
                        res = []
                        fn = d + fn
                        email = open(fn).read();
                        email = email[email.index("\n\n")::]
                        res = list(jieba.cut(email))
                        res = list(set(res))
                        self.wordlist[dirt].extend(res)
                        if fn not in self.maildic[dirt]:                           #去重并把每封邮件的分词结果存入字典
                            self.maildic[dirt][fn] = res
        except:
            self.split(trie, dirs)

def main():
    demo  = SplitEmail()
    words = demo.init_wordslist()
    trie  = demo.words_2_trie(words)
    #chars = demo.readEmail("./test/18")
    #res = []
    #demo.search_in_trie(chars, trie, res)
    demo.split(trie, ['./data/'])
    dic_of_ratio = demo.getRatio()
    for key in dic_of_ratio:
        try:
            print key.decode('utf-8'), dic_of_ratio[key]
        except:
            pass

if __name__=='__main__':
    main()