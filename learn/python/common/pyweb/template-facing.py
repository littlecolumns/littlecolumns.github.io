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
        self.editor_ns = {}
        self.output = self.element.select(".output")[0]
        self.button = self.element.select(".btn")[0]
        self.button.bind('click', self.run_click) 
        self.src = ""
        self.last_output = ""
        self.error_msg = ""

        try:
            if self.element.run == "true":
                self.run()
        except:
            pass

    def send_event(self, _type, data = {}):
        console.log("sending event", _type)
        event = None
        try:
            # non-IE
            if(_type == "success"):
                event = window.MessageEvent.new(_type)
            elif(_type == "error"):
                event = window.ErrorEvent.new(_type, data)
            
            self.element.dispatchEvent(event)
        except:
            # IE
            if(_type == "success"):
                event = doc.createEvent('MessageEvent')
            elif(_type == "error"):
                event = doc.createEvent('ErrorEvent')
            event.initEvent(_type, True, True)

        self.element.dispatchEvent(event)

    def test_solution(self):
        console.log("testing solution")
        try:
            test = self.element.test.replace("\\n","\n")
            self.editor_ns['test'] = test.strip()

            console.log("Comparing", self.last_output, "to", test.strip())
            if self.last_output and (test.strip() == self.last_output):
                self.send_event('success')
                return True

            # if eval("test == last_output", self.editor_ns):
            #     self.send_event('success')
            #     return True

            equals = eval(test, self.editor_ns)
            if type(equals) == bool and equals:
                self.send_event('success')
                return True
        except:
            console.log("exception", traceback.format_exc())
            pass

    def write(self, data):
        self.output.text += str(data)

    # run a script
    def run(self):
        self.output.text = ''
        self.src = self.editor.getValue()

        _stdout = sys.stdout
        _stderr = sys.stderr
        context = StringIO()
        sys.stdout = context
        sys.stderr = context

        self.editor_ns = {}
        try:
            exec(self.src, self.editor_ns)
            self.write(context.getvalue())
            self.error_msg = ""
        except Exception as exc:
            self.write(context.getvalue())
            self.write(traceback.format_exc())
            self.error_msg = traceback.format_exc()

        self.last_output = context.getvalue().strip()
        self.editor_ns = {
            'last_output': self.last_output,
            '_': self.last_output,
            'src': self.src,
            'error_msg': self.error_msg 
        }
        sys.stdout = _stdout
        sys.stderr = _stderr

        self.test_solution()

    def run_click(self, event):
        self.run()

facing_ids = []
# __ID_APPEND__
web_facings = [PyWebFacing(_id) for _id in facing_ids]
