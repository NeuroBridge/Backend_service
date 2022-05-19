# Backend_service
Flask service serving as connection between frontend and Solr index.

## Description and format of input and output:

https://docs.google.com/document/d/1czwoaHn0FKB0dRzv5Bz-3w-UIRnX_SXm6OeIiee7ff8/edit

## Some input examples:

For /nb_translator:

>{"query":{
        
  "description": "(Schizophrenia AND (RestingStateImaging OR RestingStateImagingProtocol)) AND NeurocognitiveTest",
  "expression": {"and":[
    {
      "and": [ 
        { "or": ["RestingStateImaging", "RestingStateImagingProtocol"] },
        "Schizophrenia"
      ]
    },
    "NeurocognitiveTest"
  ]}
},
"max_res": 3,
"min_score": 0.0 
}

For /article:

>{"pmid": 30098853, "terms": ["Schizophrenia", "NoKnownDisorder"]}
