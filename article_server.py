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
CORS(app, resources={r"/*": {"origins": "*"}})
#CORS(app, support_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'


# create a dictionary for mapping and expanding entities

global onto_dic, onto_parent_dic
onto = get_ontology("NeuroBridge_093021.owl").load()
classes = onto.classes()
onto_dic, onto_parent_dic = {}, {}

for i in classes:
    onto_dic[i.name] = [i.name]
    onto_parent_dic[i.name] = [i.name]
    if i.is_a:
            onto_parent_dic[i.name] += [i.is_a[0].name]
#    if i.subclasses():
#        dic[i.name] += [g.name for g in list(i.subclasses())]




# show detailed information of NER model's annotation
@app.route('/article', methods=['GET', 'POST'])
@cross_origin(origin='*', support_credentials=True)

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
        if 'offsets.' + term in article.keys():
          output['offset'][term] = [[article['offsets.' + term][2*i], article['offsets.' + term][2*i+1]] for i in range(int(len(article['offsets.' + term])/2))]
        else:
          output['offset'][term] = []
    return output


# retrieve metedata and labels of articles
@app.route('/nb_translator', methods=['GET', 'POST'])
@cross_origin(origin='*', support_credentials=True)

def nb_translator():
    
    
    # here we can treat filtering as a hyperparemeter
    filtering = False
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
    front_end_request = request.get_json(force=True)['query']
    targeted_entities = [i for i in onto_dic.keys() if str(front_end_request['expression']).find(i) != -1]
    q = "http://neurobridges-ml.edc.renci.org:8983/solr/NB/select?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score" + "&rows={}".format(max_res)
    # the query that can be find using a browser:
    interface_q = "http://neurobridges-ml.edc.renci.org:8983/solr/#/NB/query?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score" + "&rows={}".format(max_res)
    print(interface_q)
    res = requests.get(q)
    output = {'docs':None}
    doc_list = []
    prefix = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC"
    needed_attr = ["pmid", "pmcid", "title", "abstract", "score"]
    article_list= res.json()['response']['docs'][:max_res]
    for i in range(len(article_list)):
      #entity_not_detect = False
      #if filtering:
      #  entity_not_detect = filt_func(targeted_ent, article_list[i])
      #if not ent_not_detect:
        if article_list[i]['score'] > min_score:
            doc = {}
            for j in needed_attr:
                if j == "pmcid":
                    doc[j] = "PMC" + str(article_list[i][j][0])
                elif j == 'score':
                    doc[j] = article_list[i][j]
                else:
                    doc[j] = str(article_list[i][j][0])
            doc["pmc_link"] = prefix + str(article_list[i]['pmcid'][0])
            doc["snippet"] = ' '.join(word_tokenize(doc["abstract"])[:30]).strip()
            doc_list.append(doc)
    output['docs'] = doc_list  
    return output



def filt_func(targeted_ent, article):
  # find whether this article covers all required NBC/their parents
  ent_not_detect = False
  for ent in targeted_entities:
    if not set(onto_parent_dic[ent]) & set(article['NBC']):
      ent_not_detect = True
      break
  return ent_not_detect
  
    
    
    
def recur(expression):
               
    # use recurring algorithm to concatenate terms.
    s = []
    operator = [i for i in expression.keys() if i != 'description'][0]
    if operator == 'not':
      return '(NOT(' + recur(expression['not']) + '))'
    else:
      for i in expression[operator]:
        if type(i) == str:
          s.append('(' + '%20OR%20'.join(onto_dic[i]) + ')')
        else:
          s.append(recur(i))
      return '(' + ('%20' + operator + '%20%20').join(s) + ')'




if __name__=='__main__':

    app.run(host='0.0.0.0',debug=False,port='5000')
