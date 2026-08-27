## Restoring the Database from SQL Dump

We generally load a database backup from a JSON file by using the following command.

```
docker-compose -f local.yml run --rm django python manage.py loaddata backup.json
```

However, if the JSON file is particularly large (>1.5GB), Docker might struggle with this method. In such cases, you can use SQL dump and restore commands as an alternative.

> **Never paste real credentials, hostnames, or database endpoints into this file.** Every value
> below is a placeholder. Read the actual values from the appropriate `.envs/*/.postgres` file on
> the host at the time you run the commands.

### Steps for Using SQL Dump and Restore

1. Begin by starting only the PostgreSQL container. This prevents the Django container from making changes while the PostgreSQL container is starting up.

```
docker-compose -f local.yml up postgres
```

2. Find the container ID using `docker ps`, then enter the PostgreSQL container to execute commands.

```
$ docker ps
CONTAINER ID   IMAGE                                     COMMAND
<container-id> <postgres-image>                          "docker-entrypoint.s…"

$ docker exec -it <container-id> bash
```

3. Create a connection to the database.

```
psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

**Note**:
- For local deployment, refer to the `.envs/.local/.postgres` file for the `POSTGRES_USER` and `POSTGRES_DB` variables.
- For deployed hosts, refer to that host's `.envs/.production/.postgres` file.

4. Ensure that the database `<POSTGRES_DB>` is empty. Here's an example:

```
<POSTGRES_DB>-# \c
You are now connected to database "<POSTGRES_DB>" as user "<POSTGRES_USER>".
<POSTGRES_DB>-# \dt
Did not find any relations.
```

If the database is not empty, delete its contents to create a fresh database:

```
<POSTGRES_DB>=# \c postgres      //connect to a different database before dropping
You are now connected to database "postgres" as user "<POSTGRES_USER>".
postgres=# DROP DATABASE <POSTGRES_DB>;
DROP DATABASE
postgres=# CREATE DATABASE <POSTGRES_DB>;
CREATE DATABASE

```

5. Transfer the backup SQL dump (`backup.sql`) from your local machine to the PostgreSQL container.

```
docker cp /local/path/backup.sql <container-id>:/
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

---

## Making a backup from a deployed host

Read the database values from the host's env file — do not copy them anywhere:

```bash
ssh <host>
cat .envs/.production/.postgres     # POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

Find the running Postgres container:

```bash
docker ps
```

Dump the database. Prefer letting `pg_dump` prompt for the password (`-W`) over putting it in the
command, which would otherwise land in your shell history:

```bash
docker exec -it <container-id> pg_dump -h <POSTGRES_HOST> -U <POSTGRES_USER> -d <POSTGRES_DB> -W > backup.sql
```

### Move the backup to your local machine

```bash
scp <host>:/home/ec2-user/sde-indexing-helper/backup.sql .
```

To copy it to another host, `scp` or — if the transfer is unreliable — `rsync`:

```bash
rsync -avzP backup.sql <other-host>:/home/ec2-user/sde-indexing-helper/
```

### Restoring the backup

Bring the local containers down, then start only Postgres:

```bash
docker-compose -f local.yml down
docker-compose -f local.yml up postgres
docker ps
```

Read the target database values from the appropriate env file, then connect and recreate the
database:

```bash
docker exec -it <container-id> bash
psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

```sql
\c postgres
DROP DATABASE <POSTGRES_DB>;
CREATE DATABASE <POSTGRES_DB>;
```

Copy the dump into the container and load it:

```bash
docker cp backup.sql <container-id>:/
docker exec -it <container-id> bash
psql -U <POSTGRES_USER> -d <POSTGRES_DB> -f backup.sql
```

Finally, bring everything back up and migrate:

```bash
docker-compose -f local.yml down
docker-compose -f local.yml up --build
docker-compose -f local.yml run --rm django python manage.py migrate
```

**Note:** the `database_backup` and `database_restore` management commands documented in the
[README](./README.md) are the recommended path for routine work; the manual procedure above is for
cases those commands can't handle.
