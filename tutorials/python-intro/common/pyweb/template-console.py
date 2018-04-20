import sys
import traceback
import json
from io import StringIO
import contextlib

from browser import document as doc
from browser import window, alert, console, timer

_credits = """    Thanks to CWI, CNRI, BeOpen.com, Zope Corporation and a cast of thousands
    for supporting Python development.  See www.python.org for more information."""

_copyright = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All Rights Reserved.

Copyright (c) 2001-2013 Python Software Foundation.
All Rights Reserved.

Copyright (c) 2000 BeOpen.com.
All Rights Reserved.

Copyright (c) 1995-2001 Corporation for National Research Initiatives.
All Rights Reserved.

Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam.
All Rights Reserved."""

_license = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. Redistributions in binary
form must reproduce the above copyright notice, this list of conditions and
the following disclaimer in the documentation and/or other materials provided
with the distribution.
Neither the name of the <ORGANIZATION> nor the names of its contributors may
be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

INTRO_MSG = '<span class="intro">Type your Python code below, then hit enter to run it.</span>'
TAB = '  '
PROMPT = '<span class="prompt">&gt;&gt;&gt;</span> '
PROMPT_CONT = '<span class="prompt-cont">...</span> '
element = doc['__BASE_ID__']

def credits():
    print(_credits)
credits.__repr__ = lambda:_credits

def copyright():
    print(_copyright)
copyright.__repr__ = lambda:_copyright

def license():
    print(_license)
license.__repr__ = lambda:_license

def write(data):
    append_to_element(str(data))
    element.scrollTop = element.scrollHeight

sys.stdout.write = sys.stderr.write = write

history = []
is_static = False
try:
    is_static = element.static == 'true'
    if is_static:
        element.class_name = element.class_name + " is_static"
except:
    pass
current = 0
last_output = None
queue = ""
_status = "main" # or "block" if typing inside a block

# execution namespace
editor_ns = {
    'credits': credits,
    'copyright': copyright,
    'license': license,
    '__name__': '__main__',
    '_': None,
    'last_output': None
}

def element_value():
    return element.text

def set_element_value(text):
    element.html = text

def process_queue():
    global queue

    if not queue or len(queue) == 0:
        return

    current = queue[:1]
    queue = queue[1:]

    # If it's a return, push fake enter
    if current == "\n":
        myKeyPress(None)
    else:
        append_to_element(current)

def append_to_element(text):
    set_element_value(element.html + text)

def cursorToEnd(*args):
    _range = doc.createRange()
    _range.selectNodeContents(element)
    _range.collapse(False)
    selection = window.getSelection()
    selection.removeAllRanges()
    selection.addRange(_range)

def get_col(area):
    # returns the column num of cursor
    # it counts after hte <span>, we do -1
    # because the prompt has a space after it
    _range = window.getSelection().getRangeAt(0)
    return _range.startOffset - 1

def run_initial():
    global queue

    # It's okay to have starting whitespace so that
    # <pre> can get an enter before we start coding
    content = element_value().lstrip()
    if content == "":
        return False
    lines = content.split("\n")
    intro_and_prompt(needs_prompt=True)

    if False:
        queue = content + "\n"
    else:
        # Faux type the lines in
        for line in lines:
            if element_value()[-2:] == TAB:
                set_element_value(element.html[:-2])
            append_to_element(line)
            myKeyPress(None)

        # Remove the prompt
        if is_static:
            pieces = element.html.split("\n")
            while pieces[-1].split() == PROMPT.split():
                del pieces[-1]
            set_element_value("\n".join(pieces))

    return True

def prevent(event):
    try:
        event.preventDefault()
    except:
        pass

# def test_solution():
#     print('hello11')
#     global last_output
#     print('hello')
#     try:
#         print('hello')
#         # Testing whether the last result equals test value
#         # console.log("Do they match?")
#         if str(editor_ns['_']) == str(element.test):
#             event = window.MessageEvent.new('success')
#             element.dispatchEvent(event)
#             return True
#         # console.log("no.")
#         print('hello2')
        
#         # Test whether printed output matches
#         console.log('x',last_output,'x')
#         if last_output and str(last_output).strip() == str(element.test).strip():
#             event = window.MessageEvent.new('success')
#             element.dispatchEvent(event)
#             return True

#         # console.log("true?")
#         # Testing whether the test returns true
#         equals = eval(element.test, editor_ns)
#         if type(equals) == bool and equals:
#             event = window.MessageEvent.new('success')
#             element.dispatchEvent(event)
#             return True

#         # console.log("no.")

#     except:
#         # Test failed
#         # (probably unitialized var)
#         pass

def test_solution():
    global last_output, element, editor_ns

    try:
        test = element.test.replace("\\n","\n")

        if str(editor_ns['_']) == test:
            event = window.MessageEvent.new('success')
            element.dispatchEvent(event)
            return True

        if last_output and (test.strip() == last_output):
            event = window.MessageEvent.new('success')
            element.dispatchEvent(event)
            return True

        equals = eval(test, editor_ns)
        if type(equals) == bool and equals:
            event = window.MessageEvent.new('success')
            element.dispatchEvent(event)
            return True
    except:
        pass

def log_response(response=None):
    global last_output
    if response is not None:
        escaped = repr(response).replace("<","&lt;")
        append_to_element(escaped + '\n')

    test_solution()
    # try:
    #     # TODO can't serialize type?
    #     event = window.MessageEvent.new('message', {
    #         'data': json.dumps(response)
    #     })
    #     element.dispatchEvent(event)
    # except:
    #     pass

    # element.response = repr(response)

def process_error():
    event = window.ErrorEvent.new('error', {
        'error': sys.exc_info()[1].__class__.__name__,
        'message': str(sys.exc_info()[1])
    })
    element.dispatchEvent(event)
    append_to_element(traceback.format_exc())
    # traceback.print_exc()

def myKeyPress(event):
    global _status, current, is_static, last_output

    # When we trigger return manually we just don't send event
    run_code = not event or event.keyCode == 13
    do_tab = event and event.keyCode == 9

    if do_tab:
        prevent(event)
        append_to_element(TAB)
    elif run_code:
        src = element_value()
        if _status == "main":
            currentLine = src[src.rfind('>>>') + 4:]
        elif _status == "3string":
            currentLine = src[src.rfind('>>>') + 4:]
            currentLine = currentLine.replace('\n' + PROMPT_CONT, '\n')
        else:
            currentLine = src[src.rfind('...') + 4:]
        if _status == 'main' and not currentLine.strip():
            append_to_element('\n' + PROMPT)
            prevent(event)
            return
        append_to_element('\n')
        history.append(currentLine)
        current = len(history)
        if _status == "main" or _status == "3string":
            try:
                _stdout = sys.stdout
                _stderr = sys.stderr
                context = StringIO()
                sys.stdout = context
                sys.stderr = context
                
                _ = editor_ns['_'] = eval(currentLine, editor_ns)
                last_output = editor_ns['last_output'] = context.getvalue().strip()
                write(context.getvalue())
                log_response(_)
                append_to_element(PROMPT)
                _status = "main"
            except IndentationError:
                if(_status == "main"):
                    append_to_element(PROMPT_CONT + TAB)
                else:
                    append_to_element(PROMPT_CONT)                    
                _status = "block"
            except SyntaxError as msg:
                if str(msg) == 'invalid syntax : triple string end not found' or \
                    str(msg).startswith('Unbalanced bracket'):
                    append_to_element(PROMPT_CONT)
                    _status = "3string"
                elif str(msg) == 'eval() argument must be an expression':
                    try:
                        _stdout = sys.stdout
                        _stderr = sys.stderr
                        context = StringIO()
                        sys.stdout = context
                        sys.stderr = context
                        exec(currentLine, editor_ns)
                        last_output = editor_ns['last_output'] = context.getvalue().strip()
                        write(context.getvalue())
                        log_response()
                    except:
                        process_error()
                    append_to_element(PROMPT)
                    _status = "main"
                elif str(msg) == 'decorator expects function':
                    append_to_element(PROMPT_CONT)
                    _status = "block"
                else:
                    process_error()
                    append_to_element(PROMPT)
                    _status = "main"
            except:
                process_error()
                append_to_element(PROMPT)
                _status = "main"
        elif currentLine == "":  # end of block
            block = src[src.rfind('>>>') + 4:].splitlines()
            block = [block[0]] + [b[4:] for b in block[1:]]
            block_src = '\n'.join(block)
            # status must be set before executing code in globals()
            _status = "main"
            try:
                _stdout = sys.stdout
                _stderr = sys.stderr
                context = StringIO()
                sys.stdout = context
                sys.stderr = context
                exec(block_src, editor_ns)
                last_output = editor_ns['last_output'] = context.getvalue().strip()
                write(context.getvalue())
                log_response()
            except:
                process_error()
            append_to_element(PROMPT)
        else:
            append_to_element(PROMPT_CONT)

        cursorToEnd()
        prevent(event)

def myKeyDown(event):
    global _status, current, is_static

    if event.keyCode == 37:  # left arrow
        sel = get_col(element)
        if sel < 1:
            event.preventDefault()
            event.stopPropagation()
    elif event.keyCode == 36:  # line start
        window.getSelection().collapseToStart()
        event.preventDefault()
    elif event.keyCode == 38:  # up
        if current > 0:
            pass
            # remove current line
            # set_element_value(element_value()[:len(PROMPT)])
            # current -= 1
            # append_to_element(history[current])
        event.preventDefault()
    elif event.keyCode == 40:  # down
        if current < len(history) - 1:
            pass
        #     pos = element.selectionStart
        #     col = get_col(element)
        #     # remove current line
        #     set_element_value(element_value()[:pos - col + 4])
        #     current += 1
        #     append_to_element(history[current])
        event.preventDefault()
    elif event.keyCode == 8:  # backspace
        sel = get_col(element)
        if sel < 1:
            event.preventDefault()
            event.stopPropagation()

def insertTextAtCursor(text):
    try:
        sel = window.getSelection()
        _range = sel.getRangeAt(0)
        _range.deleteContents()
        _range.insertNode(doc.createTextNode(text))
    except:
        pass

    try:
        doc.selection.createRange().text = text
    except:
        pass
    
    cursorToEnd()

# http://jsfiddle.net/marinagon/1v63t05q/
def handlePaste(e):
    e.preventDefault()
    try:
        text = e.clipboardData.getData("text/plain")
        doc.execCommand("insertHTML", False, text)
    except:
        pass

    try:
        text = window.clipboardData.getData("Text")
        insertTextAtCursor(text)
    except:
        pass

def focus(event):
    element.focus()
    cursorToEnd()

def nothing(event):
    element.blur()
    event.preventDefault()
    event.stopPropagation()

def intro_and_prompt(needs_prompt=True):
    if not is_static:
        set_element_value(INTRO_MSG + "\n" + PROMPT)
    elif needs_prompt:
        set_element_value(PROMPT)

def attach_events():
    element.bind('keypress', myKeyPress)
    element.bind('keydown', myKeyDown)
    element.bind('click', cursorToEnd)
    element.bind('mouseover', focus)
    element.bind('paste', handlePaste)
    if is_static:
        element.bind('focus', nothing)


attach_events()

timer.set_interval(process_queue, 200)

if run_initial():
    pass
else:
    intro_and_prompt()

# v = sys.implementation.version
# element_value = "Brython %s.%s.%s on %s %s\n>>> " % (
#     v[0], v[1], v[2], window.navigator.appName, window.navigator.appVersion)
# element.focus()
# cursorToEnd()