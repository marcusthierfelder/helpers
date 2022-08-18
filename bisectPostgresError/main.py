# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import argparse
import sys
import os
import subprocess


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.

def process_table():
    #print(f'{pg_path}')
    #print(f'{args.db_name}')

    db_creds = f'user={args.db_user} password={args.db_pwd} dbname={args.db_name}'
    sqlQuery_count = f'select count(*) from {args.db_table}'


    ## suche die anzahl der einträge
    db_cmd = f'{psql_binary} -X -A "{db_creds}" -t -c "{sqlQuery_count}"'
    print(db_cmd)
    try:
        count = int(subprocess.check_output(db_cmd, shell=True).decode('utf-8').strip())
    except subprocess.CalledProcessError:
        sys.exit("count count nicht ausgeführt werden")
    print(f'->{count}<-')


    ## suche die chunks druch ob da ein fehler drin ist
    nr = 0
    chunksize = 10000
    allerrors = []
    while (nr < count):
        von = nr
        bis = min(nr+chunksize, count) - 1
        size = bis - von
        print(f'ChunkTest  {von} - {bis} ')
        errors = process_table_chunk(von, size, db_creds)
        nr = bis + 1

    print(errors)

def process_table_chunk(von, size, db_creds):
    print(f'Bisektion  {von} - {size} ')

    sqlQuery1 = f'select * from {args.db_table} order by {args.db_col} asc limit {size} offset {von}'
    sqlQuery2 = f'select {args.db_col} from {args.db_table} order by {args.db_col} asc limit {size} offset {von}'


    errors = []
    try:
        db_cmd = f'{psql_binary} -X -A "{db_creds}" -t -c "{sqlQuery1}"'
        subprocess.check_output(db_cmd, shell=True)
    except subprocess.CalledProcessError:
        if (size == 1):
            db_cmd = f'{psql_binary} -X -A "{db_creds}" -t -c "{sqlQuery2}"'
            error = subprocess.check_output(db_cmd, shell=True).decode('utf-8').strip()
            errors.append(error)
        else:
            s1 = size/2
            s2 = size-s1
            p = von + s1
            errors1 = process_table_chunk(von, s1, db_creds)
            errors2 = process_table_chunk(p, s2, db_creds)
            errors.extend(errors1)
            errors.extend(errors2)

    return errors




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('Los gehts')

    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--pg_path', action='store', help="Postgres-Verzeichnis")
    parser.add_argument('-N', '--db_name', action='store', help="db name", nargs='?', default="tomedo")
    parser.add_argument('-U', '--db_user', action='store', help="db user", nargs='?', default="tomedo")
    parser.add_argument('-P', '--db_pwd', action='store', help="db pwd", nargs='?', default="pwd")
    parser.add_argument('-t', '--db_table', action='store', help="db tabelle", nargs='?', default="change")
    parser.add_argument('-c', '--db_col', action='store', help="db spalte zum suchen", nargs='?', default="revision")

    args = parser.parse_args()

    pg_path = args.pg_path
    if not pg_path:
        pg_path = "/Applications/Postgres.app/Contents/Versions/latest"
    if not pg_path:
        pg_path = "/Applications/tomedoServerUtils/Contents/postgres"
    psql_binary = pg_path + "/bin/psql"
    if not os.path.exists(psql_binary):
        print(f'psql ist nicht da ->  {psql_binary}')
        sys.exit()


    process_table()