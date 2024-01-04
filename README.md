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

## Start service on Sterling
Currently, only the Python webapp is configured for deployment to Sterling. The image can be built and pushed to Harbor (see RENCI wiki for setup) with:

**Replace `VERSIONTAG` with the semver version**
```bash
docker build . -t containers.renci.org/neurobridges/backend-service:VERSIONTAG
docker push containers.renci.org/neurobridges/backend-service:VERSIONTAG
```

The chart can be configured in the [/kubernetes](/kubernetes/) folder, using the [`values.yaml`](/kubernetes/values.yaml) file. To install or upgrade the chart:

```bash
helm install backend-service kubernetes -n neurobridges
helm upgrade backend-service kubernetes -n neurobridges
```

If you update the application, build a new image, change the `image.tag` value to the newest tag, and run the `helm upgrade` command above. 

## Start backend service
  These files are stored in the virtual machine owned by RENCI, be sure to connect to RENCI vpn before going through the following procedure:

  ssh neurobridges-ml.edc.renci.org

  Go to projects/neurobridges/backend_service, then

### Start and stop Solr index serving for the backend:
  
 For starting, enter a new screen (for long-term processes):
 
 > screen -S solr
 
 run the following command:
 
 > /projects/neurobridges/backend_service/solr-8.11.1/bin/solr start
 
 For terminating, run the following command:
 
 > screen -r solr
 > /projects/neurobridges/backend_service/solr-8.11.1/bin/solr stop

### Start flask service:

  For starting, enter a new screen (for long-term processes):
 
  > screen -S article
 
  cd to the flask_service directory

  > cd /projects/neurobridges/backend_service/flask_service

  run the following command:
  
  > python /projects/neurobridges/backend_service/flask_service/article_server.py
  
  For terminating, go back to the screen (screen -r article):
  
  > Ctrl + C

