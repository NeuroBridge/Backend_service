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

global ONTO_DICT, ONTO_EXPA_DIC


onto = get_ontology("NeuroBridge_093021.owl").load()
classes = onto.classes()
ONTO_DICT, ONTO_EXPA_DIC = {}, {}

for i in classes:
    ONTO_DICT[i.name] = [i.name]
    ONTO_EXPA_DIC[i.name] = [i.name]
    if i.is_a:
            ONTO_EXPA_DIC[i.name] += [i.is_a[0].name]




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
    
    
    # by changing the filtering variable to true, we can apply the filtering function 
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
    targeted_entities = [i for i in ONTO_DICT.keys() if str(front_end_request['expression']).find(i) != -1]
    q = "http://neurobridges-ml.edc.renci.org:8983/solr/NB/select?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score"
    # the query that can be find using a browser:
    interface_q = "http://neurobridges-ml.edc.renci.org:8983/solr/#/NB/query?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score"
    print(interface_q)
    res = requests.get(q)
    output = {}
    prefix = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC"
    needed_attr = ["pmid", "pmcid", "title", "abstract", "score"]
    article_list= res.json()['response']['docs'][:max_res]
    
    # form response json files
    for i in range(len(article_list)):
      entity_not_detect = False
      if filtering:
        entity_not_detect = filt_func(targeted_ent, article_list[i])
      if not ent_not_detect:
        if article_list[i]['score'] > min_score:
            output["result_" + str(i)] = {}
            for j in needed_attr:
                if j == "pmcid":
                    output["result_" + str(i)][j] = "PMC" + str(article_list[i][j][0])
                elif j == 'score':
                    output["result_" + str(i)][j] = article_list[i][j]
                else:
                    output["result_" + str(i)][j] = str(article_list[i][j][0])
            output["result_" + str(i)]["pmc_link"] = prefix + str(article_list[i]['pmcid'][0])
            output["result_" + str(i)]["snippet"] = ' '.join(word_tokenize(output["result_" + str(i)]["abstract"])[:30])
    docs = {}
    docs['docs'] = output  
    return output



def filt_func(targeted_ent, article):
    
    # filtering: check whether retrieved article containing all required concepts or their parents
    # if not, delete this article from the list
    # return value is boolean
    ent_not_detect = False
    for ent in targeted_entities:
        if not set(ONTO_EXPA_DIC[ent]) & set(article['NBC']):
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
          s.append('(' + '%20OR%20'.join(ONTO_DICT[i]) + ')')
        else:
          s.append(recur(i))
      return '(' + ('%20' + operator + '%20%20').join(s) + ')'




if __name__=='__main__':

    app.run(host='0.0.0.0',debug=False,port='5000')