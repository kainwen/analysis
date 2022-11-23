

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
create table t(time timestamp, pid int,ppid int,rss int,vsz int,is_postgres boolean,sess_id int, seg_id int,comm text);
create unique index on t(time, pid);
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

-- number of processes for a session on a segment at a given time
with qes as (select * from t where is_postgres and sess_id is not null and seg_id is not null)
select
time, sess_id, seg_id,
count(pid)
from qes
group by time, sess_id, seg_id; --order by count(pid)

-- number of processes for a session on host at a given time
with qes as (select * from t where is_postgres and sess_id is not null and seg_id is not null)
select
time, sess_id, count(pid)
from qes
group by time, sess_id; --order by time

-- peak process utilizing memory at a given time
with max_mem_time as (select
                      time, max(vsz) as mem	
                      from t group by time)
select * from t where (time, vsz) in (select time, mem from max_mem_time);

-- collective memory utilization of processes on a given host/segment
select time, sum(vsz) from t group by time;
select time, sum(vsz) from t where is_postgres group by time;
select time, seg_id sum(vsz) from t where is_postgres and seg_id is not null group by time, seg_id;
