## Access Tokens
Generate your access token using https://doc.sinequa.com/en.sinequa-es.v11/Content/en.sinequa-es.how-to.access-tokens.html, then add it to a config.py as `token = <your token>`

## General API Stuff
https://doc.sinequa.com/en.sinequa-es.v11/Content/en.sinequa-es.devDoc.webservice.rest.html

## Query API
For extra details on how to use the query api, you can see

## Indexing API
Don't be fooled by the page on indexing....
https://doc.sinequa.com/en.sinequa-es.v11/Content/en.sinequa-es.devDoc.webservice.rest-indexing.html#indexing-collection

You want the page on jobs https://doc.sinequa.com/en.sinequa-es.v11/Content/en.sinequa-es.devDoc.webservice.rest-operation.html#operationcollectionStart.

## Creating Job Lists
Update config.py to contain the latest collections you want to index. Then run generate_jobs.py and it will create the parallel batches.
If you want it to run on multiple nodes, you will need to add that in two places in the file, and then you won't be able to run the lists from the masterlist, because of a sinequa bug.
