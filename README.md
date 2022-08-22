# Backend_service
Backend service serving as connection between frontend and Solr index.

## Description and format of input and output:

https://docs.google.com/document/d/1czwoaHn0FKB0dRzv5Bz-3w-UIRnX_SXm6OeIiee7ff8/edit

## Some input examples:

For /nb_translator:

>{"query":{
>        
>  "description": "(Schizophrenia AND (RestingStateImaging OR RestingStateImagingProtocol)) AND NeurocognitiveTest",
>  "expression": {"and":[
>    {
>      "and": [ 
>        { "or": ["RestingStateImaging", "RestingStateImagingProtocol"] },
>        "Schizophrenia"
>      ]
>    },
>    "NeurocognitiveTest"
>  ]}
>},
>"max_res": 3,
>"min_score": 0.0 
>}

For /article:

>{"pmid": 30098853, "terms": ["Schizophrenia", "NoKnownDisorder"]}


## Start backend service
  These files are stored in the virtual machine owned by RENCI, be sure to connect to RENCI vpn before going through the following procedure:
  Go to projects/neurobridges/backend_service, then

### Start and stop Solr index serving for the backend:
  
 For starting, run the following command:
 > solr-8.11.1/bin/solr start
 For terminating, run the following command:
 > solr-8.11.1/bin/solr stop

### Start flask service:
  For starting, run the following command:
  > nohup flask_service/article_server.py
  For terminating, run the following command:
  fuser -n tcp -k 5000

