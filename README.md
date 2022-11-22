

### Usage

```
usage: analysis.py [-h] --input INPUT --dbname DBNAME --host HOST --port PORT --user USER --tabname TABNAME

Parse Memwatch report and load it into Postgres

optional arguments:
  -h, --help         show this help message and exit
  --input INPUT      memwatch raw result
  --dbname DBNAME    database name to connect
  --host HOST        hostname to connect
  --port PORT        port to connect
  --user USER        username to connect with
  --tabname TABNAME  Table to Load data
```

### Example

Table create SQL:

```sql
create table t(time timestamp, pid int,ppid int,rss int,vsz int,is_postgres boolean,sess_id int,comm text);
```

Parse and load data:

```
python3 analysis.py --input sdw2.ps.out --dbname gpadmin --host localhost --port 5432 --user gpadmin --tabname t
```

Analyze the result:

```sql
-- find the peak
select * from t where vsz = (select max(vsz) from t);

-- find the peak QE
with qes as (select * from t where is_postgres and sess_id is not null)
select * from qes where vsz = (select max(vsz) from qes);
```