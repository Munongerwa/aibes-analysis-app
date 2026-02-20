import os
import sys

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from app import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='127.0.0.1', port=port, debug=True)