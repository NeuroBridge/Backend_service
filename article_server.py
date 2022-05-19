# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 00:05:46 2022

@author: Lenovo
"""



import json
from flask import Flask, request
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
import sys
from owlready2 import *
import requests
from flask_cors import CORS, cross_origin



app = Flask(__name__)
CORS(app)



# create a dictionary for mapping and expanding entities

global dic_sub_par
onto = get_ontology("NeuroBridge_093021.owl").load()
classes = onto.classes()
dic = {}

for i in classes:
    dic[i.name] = [i.name]
    if i.is_a:
            dic[i.name] += [i.is_a[0].name]
    if i.subclasses():
        dic[i.name] += [g.name for g in list(i.subclasses())]




# show detailed information of NER model's annotation
@app.route('/article', methods=['GET', 'POST'])
@cross_origin()

def article():
    
    query = request.get_json(force=True)
    pmid, terms = query['pmid'], query['terms']
    q =  "http://neurobridges-ml.edc.renci.org:8983/solr/NB/select?indent=true&q.op=OR&q=pmid%3A%20" + str(pmid)
    res = requests.get(q)
    article =  res.json()['response']['docs'][0]
    output = {}
    output['text'] = article['text']
    output['authors'] = article['authors']
    output['offset'] = {}
    for term in terms:
        output['offset'][term] = [[article['offsets.' + term][2*i], article['offsets.' + term][2*i+1]] for i in range(int(len(article['offsets.' + term])/2))]
    return output


# retrieve metedata and labels of articles
@app.route('/nb_translator', methods=['GET', 'POST'])
@cross_origin()

def nb_translator():
    
    keys = request.get_json(force=True).keys()
    if 'query' not in keys:
        return "Query cannot be empty."
    if "max_res" in keys:
        max_res = request.get_json(force=True)['max_res']
    else:
        max_res = 100
    if "min_score" in keys:
        min_score = request.get_json(force=True)['min_score']
    else:
        min_score = 0.0
    compact = request.get_json(force=True)['query']
    q = "http://neurobridges-ml.edc.renci.org:8983/solr/NB/select?indent=true&q.op=OR&q=NBC%3A%20" + recur(compact['expression']) + "&fl=*,%20score"
    # the query that can be find using a browser:
    # interface_q = "http://neurobridges-ml.edc.renci.org:8983/solr/#/NB/query?indent=true&q.op=OR&q=NBC%3A%20" + recur(compact['expression']) + "&fl=*,%20score"
    res = requests.get(q)
    output = {}
    prefix = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC"
    needed_attr = ["pmid", "pmcid", "title", "abstract", "score"]
    article_list= res.json()['response']['docs'][:max_res]
    for i in range(len(article_list)):
        if article_list[i]['score'] > min_score:
            output["result_" + str(i)] = {}
            for j in needed_attr:
                if j == "pmcid":
                    output["result_" + str(i)][j] = "PMC" + str(article_list[i][j][0])
                else:
                    output["result_" + str(i)][j] = article_list[i][j]
            output["result_" + str(i)]["pmc_link"] = prefix + str(article_list[i]['pmcid'][0])
            output["result_" + str(i)]["snippet"] = ' '.join(word_tokenize(output["result_" + str(i)]["abstract"][0])[:30])
    docs = {}
    docs['docs'] = output
    return output

def retrieve(q):

    # generate query and retrieve information from Solr index.

    onto = get_ontology("NeuroBridge_093021.owl").load()
    classes = onto.classes()
    dic = {}

    for i in classes:
        dic[i.name] = [i.name]
        if i.is_a:
                dic[i.name] += [i.is_a[0].name]
        if i.subclasses():
            dic[i.name] += [g.name for g in list(i.subclasses())]
    
    q_list = []
    for i in q:
        for g in dic[q]:
            q_list.append(g)
    q = q_list
    q_expression = '%20OR%20NBC%3A%20'.join(q)
    res = requests.get("http://neurobridges-ml.edc.renci.org:8983/solr/NB/select?indent=true&q.op=OR&q=NBC%3A%20" + q_expression)
    res.encoding = 'ISO-8859-1'
    prefix = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC"
    return [i['title'][0] for i in res.json()['response']['docs'][:10]]


    
    
    
def recur(dic):
               
    # use recurring algorithm to concatenate terms.
    s = []
    operator = [i for i in dic.keys() if i != 'description'][0]
    if operator == 'not':
      return '(NOT(' + recur(dic['not']) + '))'
    else:
      for i in dic[operator]:
        if type(i) == str:
          s.append('(' + '%20OR%20'.join(dic_sub_par[i]) + ')')
        else:
          s.append(recur(i))
        return '(' + ('%20' + operator + '%20%20').join(s) + ')'




if __name__=='__main__':

    app.run(host='0.0.0.0',debug=True,port='5000')