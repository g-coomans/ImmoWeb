#!/bin/env python3
#-*- coding: utf-8 -*-
# inspired by: https://www.digitalocean.com/community/tutorials/how-to-use-an-sqlite-database-in-a-flask-application

from flask import Flask, render_template, request, Response, redirect, url_for
import sqlite3

import datetime
import operator

PIC_DIR = "./static/img_cache"
LOG_FILE = "./immoDbViewer.log"
HOUSES_PER_PAGE = 30

app = Flask("ImmoDbViewer")

def get_db_connection():
    con = sqlite3.connect('immodb.sqlite')
    con.row_factory = sqlite3.Row
    return con

def log(log_text):
    stamped_log_text = f"{str(datetime.datetime.now())} - {log_text}"
    print(stamped_log_text)
    with open(LOG_FILE, 'a') as l:
        l.write(stamped_log_text+"\n")

used_db_keys = ['id', 'title', 'url', 'price_main', 'landSurface', 'surface', 'constructionYear', 'epcScore', 'primaryEnergyConsumptionPerSqm', 'street', 'number', 'postalcode', 'city', 'description', 'displayAd', 'immoProvider']
def get_all_houses(elem_to_display=30, offset=0, show_hidden=False, list_of_ids=None):
    con = get_db_connection()
    displayAd = 0 if show_hidden else 1
    if list_of_ids == None:
        rows = con.execute("SELECT * FROM ad WHERE displayAd = ? ORDER BY lastModificationDate DESC LIMIT ? OFFSET ?", (displayAd, elem_to_display, offset,)).fetchall()
    else:
        list_of_ids = [ f"\'{x}\'" for x in list_of_ids ]
        ids = ",".join(list_of_ids) if len(list_of_ids) > 1 else list_of_ids[0]
        #con.set_trace_callback(print)
        rows = con.execute(f"SELECT * FROM ad WHERE id IN ({ids}) ORDER BY lastModificationDate").fetchall()
                                              
    con.close()
    posts = []
    for row in rows:
        post = {}
        for key in used_db_keys:
            post[key] = row[key]
        mod_date = row['lastModificationDate']
        post['lastModificationDate'] = mod_date.split("T")[0] if "T" in mod_date else mod_date
        post['pictureDownloads'] = row['pictureDownloads'].split(',')
        post['datetime'] = datetime.datetime.strptime(row['lastModificationDate'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        posts.append(post)
    sorted_posts = sorted(posts, key=operator.itemgetter('datetime'), reverse=True)
    return sorted_posts
        
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * HOUSES_PER_PAGE
    posts = get_all_houses(HOUSES_PER_PAGE, offset, show_hidden=False)
    next_url = url_for('index', page=page+1) if len(posts) == HOUSES_PER_PAGE else None
    prev_url = url_for('index', page=page-1) if page > 1 else None
    return render_template('index.html', title='Mijn huis huis selectie', posts=posts, next_url=next_url, prev_url=prev_url)

@app.route('/hidden')
def hidden():
    posts = get_all_houses(elem_to_display=1000, offset=0,show_hidden=True)
    return render_template('index.html', title='Mijn huis selectie - hidden', posts=posts)

@app.route('/house/<string:house_id>',methods=['GET'])
def house(house_id):
    house_ids = house_id.split('-')
    posts = get_all_houses(list_of_ids=house_ids)
    return render_template('index.html', title='Specifieke huizen', posts=posts)

@app.route('/<string:id>/hide/', methods=('POST',))
def hide(id):
    log(f"hiding: {id}")
    con = get_db_connection()
   
    # find next id and navigate to it
    next_id = 0
    position = 0
    ids = [x['id'] for x in con.execute("SELECT id FROM ad WHERE displayAd = 1 ORDER BY lastModificationDate DESC").fetchall()]
    for idx, db_id in enumerate(ids):
        if db_id == id:
            position = idx+1
            next_id = ids[position]
            break
    page_nr = int (position / HOUSES_PER_PAGE) + 1
    # hide ad
    con.execute('UPDATE ad SET displayAd = 0 WHERE id = ?', (id,))
    con.commit()
    con.close()
    url = f"{url_for('index')}?page={str(page_nr)}#{str(next_id)}"
    return redirect(url)

@app.route('/<string:id>/unhide/', methods=('POST',))
def unhide(id):
    log(f"unhiding: {id}")
    con = get_db_connection()
    con.execute('UPDATE ad SET displayAd = 1 WHERE id = ?', (id,))
    con.commit()
    con.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=1180, host='0.0.0.0')