1. Disable the inference pipeline \- path of least resistance \- we don’t want to delete functionality  
2. Look at api indexing pipeline for context on how to start indexing and/ use same resources to start indexing web content  
3. Dhanurs Django/COSMOS cheat commands  
   1. **Run:**  
   2. docker-compose \-f local.yml build  
   3. docker-compose \-f local.yml up  
        
   5. **Docker shell:**  
   6. docker-compose \-f local.yml run \--rm django python manage.py shell\_plus

      

   7. **Migrations:**  
   8. docker-compose \-f local.yml run \--rm django python manage.py makemigrations  
   9. docker-compose \-f local.yml run \--rm django python manage.py makemigrations \--merge  
   10. docker-compose \-f local.yml run \--rm django python manage.py migrate  
   12. docker-compose \-f local.yml logs \-f celeryworker  
   13. docker-compose \-f local.yml logs \-f celerybeat  
         
       

Use scraper repo also as context \- ssm the .json file 

4. Remove references to XML config generation for sinequa  
5. Provide context of how sinequa is replaced with this new backend, purpose of this integration included