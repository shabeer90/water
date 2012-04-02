import os
import datetime
import requests
import json
from water import app
from flask import render_template, send_from_directory, redirect, session, request
from requests import post


@app.route('/save/<gistId>', methods=['POST'])
def save(gistId):

    gist = {
        'files': {
            'water.js': {
                'content': request.form.keys()
            }
        }
    }

    token = session[app.config['GITHUB_ACCESS_TOKEN_KEY']]
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    r = requests.post(app.config['GITHUB_BASE_URL'] + '/gists/' + gistId + '?' + app.config['GITHUB_ACCESS_TOKEN_KEY'] + '=' + token, data=json.dumps(gist), headers=headers)

    return json.loads(r.text)['updated_at']




@app.route('/create', methods=['POST'])
def create():
    gist = {
        'description': 'created by water, a live-coding editor (http://water.gabrielflor.it)',
        'public': 'true',
        'files': {
            'water.js': {
                'content': request.form.keys()
            }
        }
    }

    token = session[app.config['GITHUB_ACCESS_TOKEN_KEY']]
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    r = requests.post(app.config['GITHUB_BASE_URL'] + '/gists' + '?' + app.config['GITHUB_ACCESS_TOKEN_KEY'] + '=' + token, data=json.dumps(gist), headers=headers)

    return json.loads(r.text)['id']




@app.route('/')
def index():

    # from http://developer.github.com/v3/oauth/ :
    #
    # 1. Redirect users to request GitHub access
    #       GET https://github.com/login/oauth/authorize
    #
    # 2. GitHub redirects back to your site
    #       POST https://github.com/login/oauth/access_token
    #
    # 3. Use the access token to access the API
    #       GET https://api.github.com/user?access_token=...

    # do we have a token in the session?
    username = ''
    avatar = ''
    github_url = ''
    create = ''

    if app.config['GITHUB_ACCESS_TOKEN_KEY'] in session:
        # if so, are we also logged in?
        token = session[app.config['GITHUB_ACCESS_TOKEN_KEY']]
        # try to get user details from github
        r = requests.get(app.config['GITHUB_BASE_URL'] + '/user' + '?' + app.config['GITHUB_ACCESS_TOKEN_KEY'] + '=' + token)
        # convert request to json object
        jsonRequest = json.loads(r.text)
        # do we have a username?
        if 'login' in jsonRequest:
            # yes - we're logged in
            username = jsonRequest['login']
            avatar = jsonRequest['avatar_url']
            github_url = jsonRequest['html_url']
        else:
            #  no - clear session
            session[app.config['GITHUB_ACCESS_TOKEN_KEY']] = ''
    else:
        # we aren't logged in - clear session
        session[app.config['GITHUB_ACCESS_TOKEN_KEY']] = ''

    # by default, client will create code contents
    # to a gist the first time user logs in to github
    if 'create' in session:
        create = session['create']
        session['create'] = ''

    return render_template('index.html', vars=dict(
        username = username,
        avatar = avatar,
        github_url = github_url,
        create = create))




@app.route('/github-login')
def github_login():
    # take user to github for authentication
    return redirect(app.config['GITHUB_AUTHORIZE_URL'] + '?client_id=' + app.config['CLIENT_ID'] + '&scope=gist')




@app.route('/github-logged-in')
def github_logged_in():
    # get temporary code
    tempcode = request.args.get('code', '')

    # construct data and headers to send to github
    data = {'client_id': app.config['CLIENT_ID'], 'client_secret': app.config['CLIENT_SECRET'], 'code': tempcode }
    headers = {'content-type': 'application/json', 'accept': 'application/json'}

    # request an access token
    r = requests.post(app.config['GITHUB_ACCESS_TOKEN'], data=json.dumps(data), headers=headers)

    # save access token in session
    session[app.config['GITHUB_ACCESS_TOKEN_KEY']] = json.loads(r.text)[app.config['GITHUB_ACCESS_TOKEN_KEY']]

    # instruct client to create code contents to a gist
    session['create'] = True

    return redirect('/')




@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')




def versioning():
    return datetime.date.today().strftime('%y%m%d')
