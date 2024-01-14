import flask
from flask import Flask, Response, jsonify
import logging
import requests

class VannaFlaskApp:
    flask_app = None

    def __init__(self, vn):
        self.flask_app = Flask(__name__)
        self.vn = vn

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @self.flask_app.route('/api/v0/generate_sql', methods=['GET'])
        def generate_sql():
            question = flask.request.args.get('question')

            if question is None:
                return jsonify({"type": "error", "error": "No question provided"})

            # id = cache.generate_id(question=question)
            id = str(hash(question))
            sql = vn.generate_sql(question=question)

            # cache.set(id=id, field='question', value=question)
            # cache.set(id=id, field='sql', value=sql)

            return jsonify(
                {
                    "type": "sql", 
                    "id": id,
                    "text": sql,
                })

        @self.flask_app.route('/api/v0/<path:catch_all>', methods=['GET', 'POST'])
        def catch_all(catch_all):
            return jsonify({"type": "error", "error": "The rest of the API is not ported yet."})

        @self.flask_app.route('/assets/<path:filename>')
        def proxy_assets(filename):
            remote_url = f'https://vanna.ai/assets/{filename}'
            response = requests.get(remote_url, stream=True)

            # Check if the request to the remote URL was successful
            if response.status_code == 200:
                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                headers = [(name, value) for (name, value) in response.raw.headers.items() if name.lower() not in excluded_headers]
                return Response(response.content, response.status_code, headers)
            else:
                return 'Error fetching file from remote server', response.status_code

        @self.flask_app.route('/', defaults={'path': ''})
        @self.flask_app.route('/<path:path>')
        def hello(path: str):
            return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vanna.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@350&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js" type="text/javascript"></script>
    <title>Vanna.AI</title>
    <script type="module" crossorigin src="/assets/index-d29524f4.js"></script>
    <link rel="stylesheet" href="/assets/index-b1a5a2f1.css">
  </head>
  <body class="bg-white dark:bg-slate-900">
    <div id="app"></div>
  </body>
</html>
"""
        
    def run(self):
        try:
            from google.colab import output
            output.serve_kernel_port_as_window(8084)
            from google.colab.output import eval_js
            print("Your app is running at:")
            print(eval_js("google.colab.kernel.proxyPort(8084)"))
        except:
            print("Your app is running at:")
            print("http://localhost:8084")
        self.flask_app.run(host='0.0.0.0', port=8084, debug=False)