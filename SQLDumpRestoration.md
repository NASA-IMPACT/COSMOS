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

8. Log in to the SDE Indexing Helper frontend to ensure that all data has been correctly populated in the UI.
