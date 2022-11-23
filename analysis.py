#-*- coding: utf-8 -*-

import re
import argparse
from datetime import datetime
from collections import namedtuple
from pg import DB


conn_pt = re.compile(r"con([0-9]+) seg([0-9]+)")
Proc = namedtuple('Proc', ['timestamp', 'pid', 'ppid', 'rss', 'vsz', 'is_postgres', 'sess_id', 'seg_id', 'comm'])

def get_session_seg_id(comm):
    m = conn_pt.findall(comm)
    if m:
        return int(m[0][0]), int(m[0][1])
    else:
        return None, None

def parse_file(path):
    samples = []
    current_ts = None
    is_head = False
    with open(path) as f:
        for line in f:
            if is_head:
                is_head = False
                continue
            # skip blank
            st = line.strip()
            if not st: continue
            # parse timestamp
            if st.startswith(">>>") and st.endswith("<<<"):
                Y,M,D,h,m,s = [int(i) for i in st.strip(">>>").strip("<<<").split(":")]
                current_ts = datetime(2000+Y,M,D,h,m,s)
                is_head = True
                continue

            # normal lines here
            ls = st.split()
            pid, ppid, rss, vsz = ls[:4]
            comm = " ".join(ls[12:])
            is_postgres = "postgres" in comm
            sess_id, seg_id = get_session_seg_id(comm)
            proc = Proc(current_ts.strftime('%Y%m%d %H:%M:%S'), int(pid), int(ppid), int(rss),
                        int(vsz), is_postgres, sess_id, seg_id, comm)
            samples.append(proc)

        return samples

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def load_to_pg(host, port, dbname, user, tabname, samples):
    db = DB(host=host, port=port, dbname=dbname, user=user)
    for ss in batch(samples, 10000):
        db.inserttable(tabname, ss)
    db.close()
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse Memwatch report and load it into Postgres')
    parser.add_argument('--input', type=str, help='memwatch raw result', required=True)
    parser.add_argument('--dbname', type=str, help='database name to connect', required=True)
    parser.add_argument('--host', type=str, help='hostname to connect', required=True)
    parser.add_argument('--port', type=int, help='port to connect', required=True)
    parser.add_argument('--user', type=str, help='username to connect with', required=True)
    parser.add_argument('--tabname', type=str, help='Table to Load data', required=True)

    args = parser.parse_args()
    # create table t(time timestamp, pid int,ppid int,rss int,vsz int,
    #                is_postgres boolean,sess_id int,seg_id int,comm text);
    s = parse_file(args.input)
    load_to_pg(args.host, args.port, args.dbname, args.user, args.tabname, s)
