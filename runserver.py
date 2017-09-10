# -*- coding:utf-8 -*-

from storm import app


@app.route('/favicon.ico')
def fav():
    return ''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7777)
