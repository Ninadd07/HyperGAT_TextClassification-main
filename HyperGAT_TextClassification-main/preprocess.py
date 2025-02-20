import nltk
import numpy as np
import pickle
from collections import Counter
from nltk import tokenize
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from sklearn.utils import class_weight
from nltk.wsd import lesk
import random
import json
from utils import clean_document, show_statisctic
from utils import clean_str_simple_version

def read_file(dataset, LDA=True):
    doc_content_list = []
    doc_sentence_list = []
    f = open('trydata/' + dataset + '_corpus.txt', 'rb')

    for line in f.readlines():
        doc_content_list.append(line.strip().decode('latin1'))
        doc_sentence_list.append(tokenize.sent_tokenize(clean_str_simple_version(doc_content_list[-1], dataset)))
    f.close()

    doc_content_list = clean_document(doc_sentence_list, dataset)

    max_num_sentence = show_statisctic(doc_content_list)

    doc_train_list_original = []
    doc_test_list_original = []
    labels_dic = {}
    label_count = Counter()

    i = 0
    f = open('trydata/' + dataset + '_labels.txt', 'r')
    lines = f.readlines()
    for line in lines:
        temp = line.strip().split("\t")
        if temp[1].find('test') != -1:
            doc_test_list_original.append((doc_content_list[i], temp[2]))
        elif temp[1].find('train') != -1:
            doc_train_list_original.append((doc_content_list[i], temp[2]))
        if not temp[2] in labels_dic:
            labels_dic[temp[2]] = len(labels_dic)
        label_count[temp[2]] += 1
        i += 1

    f.close()
    print(label_count)

    word_freq = Counter()
    word_set = set()
    for doc_words in doc_content_list:
        for words in doc_words:
            for word in words:
                word_set.add(word)
                word_freq[word] += 1

    vocab = list(word_set)
    vocab_size = len(vocab)

    vocab_dic = {}
    for i in word_set:
        vocab_dic[i] = len(vocab_dic) + 1

    print('Total_number_of_words: ' + str(len(vocab)))
    print('Total_number_of_categories: ' + str(len(labels_dic)))

    doc_train_list = []
    doc_test_list = []

    for doc, label in doc_train_list_original:
        temp_doc = []
        for sentence in doc:
            temp = []
            for word in sentence:
                temp.append(vocab_dic[word])
            if temp :
                temp_doc.append(temp)
        if temp_doc :
            doc_train_list.append((temp_doc, labels_dic[label]))

    for doc, label in doc_test_list_original:
        temp_doc = []
        for sentence in doc:
            temp = []
            for word in sentence:
                temp.append(vocab_dic[word])
            if temp :
                temp_doc.append(temp)
        if temp_doc :
            doc_test_list.append((temp_doc, labels_dic[label]))

    keywords_dic = {}
    if LDA:
        keywords_dic_original = pickle.load(open('trydata/' + dataset + '_LDA.p', "rb"))

        for i in keywords_dic_original:
            if i in vocab_dic:
                keywords_dic[vocab_dic[i]] = keywords_dic_original[i]

    train_set_y = [j for i, j in doc_train_list]

    # Compute class weights using NLTK's class_weight
    class_weights = class_weight.compute_class_weight(class_weight='balanced', classes=np.unique(train_set_y), y=train_set_y)
    
    # Compute class weights using scikit-learn's class_weight
    # class_weights = class_weight.compute_class_weight('balanced', np.unique(train_set_y), train_set_y)
    return doc_content_list, doc_train_list, doc_test_list, vocab_dic, labels_dic, max_num_sentence, keywords_dic, class_weights


def loadGloveModel(gloveFile, vocab_dic, matrix_len):
    print("Loading Glove Model")
    with open(gloveFile, 'r', encoding='utf-8') as f:
        gloveModel = {}
        glove_embedding_dimension = 0
        for line in f:
            splitLine = line.split()
            word = splitLine[0]
            glove_embedding_dimension = len(splitLine[1:])
            embedding = np.array([float(val) for val in splitLine[1:]])
            gloveModel[word] = embedding

    weights_matrix = np.zeros((matrix_len, glove_embedding_dimension))
    words_found = 0

    for word, index in vocab_dic.items():
        if word in gloveModel:
            weights_matrix[index] = gloveModel[word]
            words_found += 1
        else:
            weights_matrix[index] = np.zeros(glove_embedding_dimension)

    print("Total ", len(vocab_dic), " words")
    print("Done.", words_found, " words loaded from", gloveFile)

    return weights_matrix