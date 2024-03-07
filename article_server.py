# -*- coding: utf-8 -*-
"""
author: Xiaochen Wang
update on Feb 22 by Jiaming Qu
"""

from flask import Flask, request, jsonify
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
import sys
from owlready2 import *
import requests
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

load_dotenv()
assert(os.environ.get('solr') != None), "Missing solr environment variable"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
#CORS(app, support_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'


# create a dictionary for mapping and expanding entities
global onto_dic, onto_parent_dic
onto = get_ontology("NeuroBridge_032423.owl").load()
classes = onto.classes()
onto_dic, onto_parent_dic = {}, {}

for i in classes:
    onto_dic[i.name] = [i.name]
    onto_parent_dic[i.name] = [i.name]
    if i.is_a:
            onto_parent_dic[i.name] += [i.is_a[0].name]

# A route added for kubernetes
@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify(""), 200

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
    # targeted_entities = [i for i in onto_dic.keys() if str(front_end_request['expression']).find(i) != -1]

    q = f"{os.environ.get('solr')}/solr/NB/select?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score" + "&rows={}".format(max_res)

    res = requests.get(q)
    # prepare output documents
    doc_list = []
    article_list= res.json()['response']['docs'][:max_res]
    for i in range(len(article_list)):
        per_article = article_list[i]
        if per_article['score'] > min_score:
            doc = {}
            doc["pmid"] = per_article["pmid"]
            doc["pmcid"] = f"PMC{per_article['pmcid']}"
            doc["score"] = per_article["score"]
            doc["title"] = str(per_article["title"][0])
            doc["abstract"] = str(per_article["abstract"][0])
            doc["pmc_link"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{per_article['pmcid']}"
            doc["snippet"] = ' '.join(word_tokenize(doc["abstract"])[:30]).strip()
            doc_list.append(doc)
    output = dict()
    output['docs'] = doc_list
    return output

# flywheel dataset article return
@app.route('/flywheel', methods=['GET', 'POST'])
@cross_origin(origin='*', support_credentials=True)
def flywheel():

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
    # targeted_entities = [i for i in onto_dic.keys() if str(front_end_request['expression']).find(i) != -1]

    q = f"{os.environ.get('solr')}/solr/Flywheel/select?indent=true&q.op=OR&q=NBC%3A%20" + recur(front_end_request['expression']) + "&fl=*,%20score" + "&rows={}".format(max_res)

    res = requests.get(q)
    # prepare output documents
    doc_list = []
    article_list= res.json()['response']['docs'][:max_res]
    for i in range(len(article_list)):
        per_article = article_list[i]
        if per_article['score'] > min_score:
            doc = {}
            # add other fields in future releases
            doc["id"] = per_article["id"]
            doc["summary"] = per_article["summary"]
            doc_list.append(doc)

    output = dict()
    output['docs'] = doc_list
    return output

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
    app.run(host='0.0.0.0',debug=False,port=os.environ.get('port'))
