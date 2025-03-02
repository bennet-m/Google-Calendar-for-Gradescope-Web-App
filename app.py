import threading
from flask import Flask, Response
from gradeSync import main  # Assuming main.main is your function

app = Flask(__name__)

@app.route('/')
def run_background():
    # Start the main() function in a background thread
    thread = threading.Thread(target=main)
    thread.start()
    
    # Return an HTTP 202 Accepted response indicating the task has started
    return Response("Task started", status=202, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)