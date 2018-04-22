import sys
import time
import traceback
import dis
from io import StringIO

from browser import document as doc, window, alert, console

def to_str(xx):
    return str(xx)

class PyWebFacing:

    def __init__(self, _id):
        self.element = doc[_id]
        self.editor = window.ace.edit(_id + "-editor")

        self.output = self.element.select(".output")[0]
        self.button = self.element.select(".btn")[0]
        self.button.bind('click', self.run_click) 

        try:
            if self.element.run == "true":
                self.run()
        except:
            pass

    def write(self, data):
        self.output.text += str(data)

    # run a script
    def run(self):
        self.output.text = ''
        src = self.editor.getValue()

        _stdout = sys.stdout
        _stderr = sys.stderr
        context = StringIO()
        sys.stdout = context
        sys.stderr = context

        try:
            ns = {}
            exec(src, ns)
            self.write(context.getvalue())
        except Exception as exc:
            self.write(context.getvalue())
            self.write(traceback.format_exc())

        sys.stdout = _stdout
        sys.stderr = _stderr

    def run_click(self, event):
        self.run()

facing_ids = []
# __ID_APPEND__
web_facings = [PyWebFacing(_id) for _id in facing_ids]
