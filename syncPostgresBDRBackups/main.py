# -*- coding: utf-8 -*-
#
# Multiserver dbs mergen


import argparse
import fnmatch
import gzip
import os
import re
import shutil
import subprocess
import sys

import multiprocessing as mp


def process_tables(db_path, pg_path, multiprocessing):
    db1 = db_path + "/db1"
    db2 = db_path + "/db2"
    out = db_path + "/out"
    tmp = db_path + "/tmp"

    # sind die ordner ok
    if not os.path.exists(db1):
        print(f'Folder nicht da:  {db1}  breche ab')
        sys.exit()

    if not os.path.exists(db2):
        print(f'Folder nicht da:  {db2}  breche ab')
        sys.exit()

    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)

    tocname = "toc.dat"
    toc = os.path.join(db1, tocname)
    if not os.path.isfile(toc):
        print(f'File ist nicht da:  {toc}  breche ab')
        sys.exit()
    shutil.copy(toc, os.path.join(out, tocname))
    toc = os.path.join(db2, tocname)
    if not os.path.isfile(toc):
        print(f'File ist nicht da:  {toc}  breche ab')
        sys.exit()

    # mapping file : tabellenname
    toc_map = parse_toc_file(db1, db2, pg_path)

    for file1 in toc_map.keys():
        file2 = toc_map[file1]["corresponding_file"]
        print(f'=== {file1} .. {file2} ===')
        process_table(db1, file1, db2, file2, tmp, out, toc_map[file1])


'''    # jetzt die daten
    gz_filenames1 = sorted(fnmatch.filter(os.listdir(db1), '*.gz'))
    print(f'Files1:  {gz_filenames1}')

    gz_filenames2 = sorted(fnmatch.filter(os.listdir(db2), '*.gz'))
    print(f'Files2:  {gz_filenames2}')

    if len(gz_filenames1)!=len(gz_filenames2):
        print(f'db2 passen nicht zusammen')
        sys.exit()


    my_range = range(len(gz_filenames1))
    #pos = gz_filenames1.index("13359.dat.gz")
    #my_range = range(pos,pos+1)


    if multiprocessing:
        arguments = []
        for i in my_range:
            print(f'=== {i} ===')
            dict = {}
            dict["db1"] = db1
            dict["gz_filename1"] = gz_filenames1[i]
            dict["db2"] = db2
            dict["gz_filename2"] = gz_filenames2[i]
            dict["tmp"] = tmp
            dict["out"] = out
            #dict["table"] = toc_map[gz_filenames1[i]]
            arguments.append(dict)

        pool = mp.Pool(mp.cpu_count())
        pool.map(process_table_wrapper, arguments)
        pool.close()
    else:
        for i in my_range:
            print(f'=== {i} ===')
            process_table(db1, gz_filenames1[i], db2, gz_filenames2[i], tmp, out, toc_map[gz_filenames1[i]])'''


def parse_toc_file(db1, db2, pg_path):
    pg_restore = pg_path + "/bin/pg_restore"
    if not os.path.isfile(pg_restore):
        print(f'File ist nicht da:  {pg_restore}  breche ab')
        sys.exit()

    output = subprocess.check_output([pg_restore, "-l", db1, "-F", "d", "-a"]).decode("utf-8")
    # ACHTUNG: die 15 ist eine annahme ... macht alles einfacher
    data1 = output.split("\n")[15:]

    output = subprocess.check_output([pg_restore, "-l", db2, "-F", "d", "-a"]).decode("utf-8")
    data2 = output.split("\n")[15:]

    # für das nächste mal ... brauchen wir evtl andere
    to_one_tables = ["patientendetailsrelationen_frueherkennungsuntersuchungen",
                     "patientendetailsrelationen_karteieintraege",
                     "patientendetailsrelationen_verordnungen",
                     "patientendetailsrelationen_kvscheine",
                     "patientendetails_arzthistorie",
                     "patientendetails_caves",
                     "patientendetails_patientdetailsinfoelemente"]

    ignore_tables = ["change",
                     "globalchange",
                     "globalchangeconversion"]

    ret = {}
    for line1 in data1:
        comps1 = line1.split(";")
        if len(comps1) != 2:
            continue
        comps2 = comps1[1].split(" ")
        if len(comps2) != 8:
            sys.exit("error comps2")

        table1 = comps2[6]
        dict = {"table": table1, "rel": 0}
        if table1 in ignore_tables:
            dict["rel"] = -1
        elif "_" in table1:
            dict["rel"] = 1
            if table1 in to_one_tables:
                dict["rel"] = 2

        ret[comps1[0] + ".dat.gz"] = dict

        # andere datei rausfinden
        for line2 in data2:
            comps1 = line2.split(";")
            if len(comps1) != 2:
                continue
            comps2 = comps1[1].split(" ")
            if len(comps2) != 8:
                sys.exit("error comps2")

            table2 = comps2[6]
            if table2 == table1:
                dict["corresponding_file"] = comps1[0] + ".dat.gz"

    return ret


def process_table_wrapper(dict):
    process_table(dict["db1"], dict["gz_filename1"], dict["db2"], dict["gz_filename2"], dict["tmp"], dict["out"],
                  dict["table"])


def process_table(db1, gz_filename1, db2, gz_filename2, tmp, out, table):
    nr = gz_filename1.replace('.dat.gz', '')

    tmp_filename1 = "db1_" + nr + ".dat"
    tmp_filename2 = "db2_" + nr + ".dat"
    tmp_filename3 = "out_" + nr + ".dat"

    print(f'{table["table"]}  =>  {table["rel"]}')
    if table["rel"] == -1:
        if not os.path.exists(os.path.join(db1, gz_filename1)):
            print(f'Datei1 {gz_filename1} existiert nicht')
            return

        print(f'only move')
        shutil.copy(os.path.join(db1, gz_filename1), os.path.join(out, gz_filename1))
    else:

        if not os.path.exists(os.path.join(db1, gz_filename1)):
            print(f'Datei1 {gz_filename1} existiert nicht')
            return
        if not os.path.exists(os.path.join(db2, gz_filename2)):
            print(f'Datei2 {gz_filename2} existiert nicht')
            return

        file1 = unzip_file(db1, gz_filename1, tmp, tmp_filename1)
        file2 = unzip_file(db2, gz_filename2, tmp, tmp_filename2)

        data = merge_files(file1, file2, table)

        write_data_to_file(data, os.path.join(tmp, tmp_filename3))
        zip_file(tmp, tmp_filename3, out, gz_filename1)

        os.remove(os.path.join(tmp, tmp_filename1))
        os.remove(os.path.join(tmp, tmp_filename2))
        os.remove(os.path.join(tmp, tmp_filename3))


def merge_files(file1, file2, table):
    data1 = read_file_to_data(file1)
    data2 = read_file_to_data(file2)

    data = []
    if table["rel"] == 0:
        data = union_data_via_ident(data1[:len(data1) - 3], data2[:len(data2) - 3], 0)
    elif table["rel"] == 1:
        data = union_data_via_full(data1[:len(data1) - 3], data2[:len(data2) - 3])
    elif table["rel"] == 2:
        data = union_data_via_ident(data1[:len(data1) - 3], data2[:len(data2) - 3], 1)
    else:
        data = data1

    data.extend(data1[(len(data1) - 3):])
    # print(f'{data}')

    print(f'{len(data1)} U {len(data2)} => {len(data)} ')
    return data


def union_data_via_ident(data1, data2, pos):
    # 1. eine map von data1  a la  ident: zeile
    map = {}
    for line in data1:
        comps = re.split(r'\t+', line.strip())
        ident = comps[pos]
        if pos == 0 and not ident.isnumeric():
            ident = comps[pos + 1]
        # if not ident.isnumeric():
        # sys.exit("ident not nummeric")
        map[ident] = line

    # 2. durch data2 gehen und schaun ob die ident im map existiert
    counter = 0
    for line in data2:
        comps = re.split(r'\t+', line.strip())
        ident = comps[pos]
        if pos == 0 and not ident.isnumeric():
            ident = comps[pos + 1]
        # if not ident.isnumeric():
        # sys.exit("ident not nummeric")
        if ident not in map:
            counter += 1
            map[ident] = line

    if counter > 0:
        print(f'ACHTUNG  {counter}  rows inserted   ...   ident')

    # 3. map wieder in ein data
    data = []
    for key in map:
        data.append(map[key])

    return data


def union_data_via_full(data1, data2):
    # 1. eine map von data1
    map = {}
    for line in data1:
        map[line] = line

    # 2. durch data2 gehen
    counter = 0
    for line in data2:
        if line not in map:
            counter += 1
            map[line] = line

    if counter > 0:
        print(f'ACHTUNG  {counter}  rows inserted   ...   join-tabelle')

    # 3. map wieder in ein data
    data = []
    for key in map:
        data.append(map[key])

    return data


def read_file_to_data(file):
    f_in = open(file, "r")
    data = f_in.readlines()
    f_in.close()
    return data


def write_data_to_file(data, file):
    f_out = open(file, "w+")
    f_out.writelines(data)
    f_out.close()


def unzip_file(path, filename, out_path, out_filename):
    file = os.path.join(path, filename)
    out_file = os.path.join(out_path, out_filename)
    with gzip.open(file, 'rb') as f_in:
        with open(out_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f'unzip  {file}  =>  {out_file}   ({os.path.getsize(out_file)})')
    return out_file


def zip_file(path, filename, out_path, out_filename):
    file = os.path.join(path, filename)
    out_file = os.path.join(out_path, out_filename)
    print(f'zip  {file}  =>  {out_file}   ({os.path.getsize(file)})')
    with gzip.open(out_file, 'wb') as f_out:
        with open(file, 'rb') as f_in:
            shutil.copyfileobj(f_in, f_out)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db_path', action='store',
                        help="Verzeichnis wo beide datenbanken als  db1/  und  /db2/  liegen")
    parser.add_argument('-p', '--pg_path', action='store', help="Postgres-Verzeichnis")
    parser.add_argument('-m', '--multiprocessing', action='store_true', help="mit multiprocessing")
    args = parser.parse_args()

    db_path = args.db_path
    if not db_path:
        db_path = os.getcwd()

    pg_path = args.pg_path
    if not pg_path:
        pg_path = "/Applications/Postgres.app/Contents/Versions/latest"

    process_tables(db_path, pg_path, args.multiprocessing)
