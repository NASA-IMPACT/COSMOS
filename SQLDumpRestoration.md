## Restoring the Database from SQL Dump

We generally load a database backup from a JSON file by using the following command.

```
docker-compose -f local.yml run --rm django python manage.py loaddata backup.json
```

However, if the JSON file is particularly large (>1.5GB), Docker might struggle with this method. In such cases, you can use SQL dump and restore commands as an alternative.

### Steps for Using SQL Dump and Restore

1. Begin by starting only the PostgreSQL container. This prevents the Django container from making changes while the PostgreSQL container is starting up.

```
docker-compose -f local.yml up postgres
```

2. Find the container ID using `docker ps`, then enter the PostgreSQL container to execute commands.

```
$ docker ps
CONTAINER ID   IMAGE                                     COMMAND
23d33f22cc43   sde_indexing_helper_production_postgres   "docker-entrypoint.s…"

$ docker exec -it 23d33f22cc43 bash
```

3. Create a connection to the database.

```
psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

**Note**:
- For local deployment, refer to the `.envs/.local/.postgres` file for the `POSTGRES_USER` and `POSTGRES_DB` variables.
- For production deployment, refer to the `.envs/.production/.postgres` file.

4. Ensure that the database `<POSTGRES_DB>` is empty. Here's an example:

```
sde_indexing_helper-# \c
You are now connected to database "sde_indexing_helper" as user "VnUvMKBSdk...".
sde_indexing_helper-# \dt
Did not find any relations.
```

If the database is not empty, delete its contents to create a fresh database:

```
sde_indexing_helper=# \c postgres      //connect to a different database before dropping
You are now connected to database "postgres" as user "VnUvMKBSdk....".
postgres=# DROP DATABASE sde_indexing_helper;
DROP DATABASE
postgres=# CREATE DATABASE sde_indexing_helper;
CREATE DATABASE

```

5. Transfer the backup SQL dump (`backup.sql`) from your local machine to the PostgreSQL container.

```
docker cp /local/path/backup.sql 23d33f22cc43:/
```

6. Import the SQL dump into the PostgreSQL container.

```
psql -U <POSTGRES_USER> -d <POSTGRES_DB> -f backup.sql
```

**Note**: To create a SQL dump of your PostgreSQL database, use the following command:

```
pg_dump -U <POSTGRES_USER> -W -F p -f backup.sql <POSTGRES_DB>
```

7. Bring up all containers at once, and create a superuser account for logging in.

```
docker-compose -f local.yml up
docker-compose -f local.yml run --rm django python manage.py createsuperuser
```

8. Log in to the COSMOS frontend to ensure that all data has been correctly populated in the UI.



# making the backup

```bash
ssh sde
cat .envs/.production/.postgres
```

find the values for the variables:
POSTGRES_HOST=sde-indexing-helper-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=this_is_A_web_application_built_in_2023

```bash
docker ps
```

b3fefa2c19fb

note here that you need to put the
```bash
docker exec -t your_postgres_container_id pg_dump -U your_postgres_user -d your_database_name > backup.sql
```
```bash
docker exec -t container_id pg_dump -h host -U user -d database -W > prod_backup.sql
```

docker exec -t b3fefa2c19fb env PGPASSWORD="this_is_A_web_application_built_in_2023" pg_dump -h sde-indexing-helper-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com -U postgres -d postgres > prod_backup.sql

# move the backup to local
 go back to local computer and scp the file

```bash
scp sde:/home/ec2-user/sde_indexing_helper/prod_backup.sql .
```
scp prod_backup.sql sde_staging:/home/ec2-user/sde-indexing-helper
if you have trouble transferring the file, you can use rsync:
rsync -avzP prod_backup.sql sde_staging:/home/ec2-user/sde-indexing-helper/

# restoring the backup
bring down the local containers
```bash
docker-compose -f local.yml down
docker-compose -f local.yml up postgres
docker ps
```

find the container id

c11d7bae2e56

find the local variables from
cat .envs/.production/.postgres
POSTGRES_HOST=sde-indexing-helper-staging-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=sde_staging
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres


```bash
docker exec -it <container id> bash
```
docker exec -it c11d7bae2e56 bash

## do all the database shit you need to


psql -U <POSTGRES_USER> -d <POSTGRES_DB>
psql -U postgres -d sde_staging
or, if you are on one of the servers:
psql -h sde-indexing-helper-staging-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com -U postgres -d postgres

\c postgres
DROP DATABASE sde_staging;
CREATE DATABASE sde_staging;

# do the backup

```bash
docker cp prod_backup.sql c11d7bae2e56:/
docker exec -it c11d7bae2e56 bash
```

```bash
psql -U <POSTGRES_USER> -d <POSTGRES_DB> -f backup.sql
```
psql -U VnUvMKBSdkoFIETgLongnxYHrYVJKufn -d sde_indexing_helper -f prod_backup.sql

psql -h sde-indexing-helper-staging-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com -U postgres -d postgres -f prod_backup.sql
pg_restore -h sde-indexing-helper-staging-db.c3cr2yyh5zt0.us-east-1.rds.amazonaws.com -U postgres -d postgres prod_backup.sql



docker down

docker up build

migrate

down

up
