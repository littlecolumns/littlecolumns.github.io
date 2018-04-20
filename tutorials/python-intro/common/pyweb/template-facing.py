import sys
import time
import traceback
import dis
from io import StringIO

from browser import document as doc, window, alert, console

element = doc['__BASE_ID__']
editor = window.ace.edit("__EDITOR_ID__")
output = element.select(".output")[0]
button = element.select(".btn")[0]


def write(data):
    output.text += str(data)

def to_str(xx):
    return str(xx)

# run a script, in global namespace if in_globals is True
def run():
    output.text = ''
    src = editor.getValue()

    _stdout = sys.stdout
    _stderr = sys.stderr
    context = StringIO()
    sys.stdout = context
    sys.stderr = context

    try:
        ns = {}
        exec(src, ns)
        write(context.getvalue())
    except Exception as exc:
        console.log('exception')
        write(traceback.format_exc())

def run_click(event):
    run()

button.bind('click', run_click) 

try:
    if element.run == "true":
        run()
except:
    pass