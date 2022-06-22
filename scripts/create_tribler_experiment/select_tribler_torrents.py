"""
Read random torrent titles from the database and write them to a CSV file.
"""
import sqlite3

NUM_TORRENTS = 1000

conn = None
try:
    conn = sqlite3.connect("data/metadata.db")
except sqlite3.Error as e:
    print(e)
    exit(1)


keys = set()


cur = conn.cursor()
print("Executing query...")
cur.execute("SELECT title FROM ChannelNode WHERE metadata_type = 300 ORDER BY RANDOM() LIMIT %d;" % NUM_TORRENTS)
print("Fetching rows...")
rows = cur.fetchall()
with open("data/torrents_%d.txt" % NUM_TORRENTS, "w") as out_file:
    for row in rows:
        title = row[0].replace("\n", "")
        out_file.write("%s\n" % title)
