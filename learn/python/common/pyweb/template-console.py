import sys
import traceback
import json
from io import StringIO

from browser import document as doc
from browser import window, alert, console, timer

INTRO_MSG = """<span class="intro">Type your Python code below,
then hit enter to run it.</span>"""
TAB = '  '
PROMPT = '<span class="prompt">&gt;&gt;&gt;</span> '
PROMPT_CONT = '<span class="prompt-cont">...</span> '

ERR_INVALID_SYNTAX = 'invalid syntax : triple string end not found'
ERR_EVAL_EXPRESSION = 'eval() argument must be an expression'


class PyWebConsole:

    def __init__(self, _id):
        self._id = _id
        self.element = doc[_id]
        parent = self.element.parentNode
        self.refresh_button = parent.parentNode.select(".console-refresh")[0]
        self.original_html = self.element.html

        self.history = []
        self.is_static = False

        try:
            self.is_static = self.element.static == 'true'
            if self.is_static:
                self.element.class_name = self.element.class_name + " is_static"  # noqa
        except:
            pass

        self.attach_events()
        self.refresh()
        # timer.set_interval(self.process_queue, 200)

    def refresh(self, event=None):
        if event:
            self.element.html = self.original_html

        self.editor_ns = {
            '__name__': '__main__',
            '_': None,
            'last_output': None
        }

        self.current = 0
        self.last_output = None
        self.queue = ""
        self._status = "main"

        if self.run_initial():
            pass
        else:
            self.intro_and_prompt()

    def write(self, data):
        self.append_to_element(str(data))
        self.element.scrollTop = self.element.scrollHeight

    def element_value(self):
        return self.element.text

    def set_element_value(self, text):
        self.element.html = text

    def process_queue(self):
        if not self.queue or len(self.queue) == 0:
            return

        current = self.queue[:1]
        queue = self.queue[1:]

        # If it's a return, push fake enter
        if current == "\n":
            self.myKeyPress(None)
        else:
            self.append_to_element(current)

    def append_to_element(self, text):
        self.set_element_value(self.element.html + text)

    def cursorToEnd(self, event=None):
        _range = doc.createRange()
        _range.selectNodeContents(self.element)
        _range.collapse(False)
        selection = window.getSelection()
        selection.removeAllRanges()
        selection.addRange(_range)

    def get_col(self):
        # returns the column num of cursor
        # it counts after hte <span>, we do -1
        # because the prompt has a space after it
        _range = window.getSelection().getRangeAt(0)
        return _range.startOffset - 1

    def run_initial(self):
        # It's okay to have starting whitespace so that
        # <pre> can get an enter before we start coding
        content = self.element_value().lstrip()
        if content == "":
            return False
        lines = content.split("\n")
        self.intro_and_prompt(needs_prompt=True)

        if False:
            self.queue = content + "\n"
        else:
            # Faux type the lines in
            for line in lines:
                if self.element_value()[-2:] == TAB:
                    self.set_element_value(self.element.html[:-2])
                self.append_to_element(line)
                self.myKeyPress(None)

            # Remove the prompt
            if self.is_static:
                pieces = self.element.html.split("\n")
                while pieces[-1].split() == PROMPT.split():
                    del pieces[-1]
                self.set_element_value("\n".join(pieces))

        return True

    def prevent(self, event):
        try:
            event.preventDefault()
        except:
            pass

    def send_event(self, _type, data={}):
        event = None
        try:
            # non-IE
            if(_type == "success"):
                event = window.MessageEvent.new(_type, data)
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
        try:
            test = self.element.test.replace("\\n", "\n")

            if str(self.editor_ns['_']) == test:
                self.send_event('success')
                return True

            if self.last_output and (test.strip() == self.last_output):
                self.send_event('success')
                return True

            equals = eval(test, self.editor_ns)
            if type(equals) == bool and equals:
                self.send_event('success')
                return True
        except:
            pass

    def log_response(self, response=None):
        if response is not None:
            escaped = repr(response).replace("<", "&lt;")
            self.append_to_element(escaped + '\n')

        self.test_solution()

    def process_error(self):
        data = {
            'error': sys.exc_info()[1].__class__.__name__,
            'message': str(sys.exc_info()[1])
        }
        self.send_event('error', data)
        self.append_to_element(traceback.format_exc())

    def myKeyPress(self, event):
        _stdout = sys.stdout
        _stderr = sys.stderr
        context = StringIO()
        sys.stdout = context
        sys.stderr = context

        # When we trigger return manually we just don't send event
        run_code = not event or event.keyCode == 13
        do_tab = event and event.keyCode == 9

        if do_tab:
            self.prevent(event)
            self.append_to_element(TAB)
        elif run_code:
            src = self.element_value()
            if self._status == "main":
                currentLine = src[src.rfind('>>>') + 4:]
            elif self._status == "3string":
                currentLine = src[src.rfind('>>>') + 4:]
                currentLine = currentLine.replace('\n' + PROMPT_CONT, '\n')
            else:
                currentLine = src[src.rfind('...') + 4:]
            if self._status == 'main' and not currentLine.strip():
                self.append_to_element('\n' + PROMPT)
                self.prevent(event)
                sys.stdout = _stdout
                sys.stderr = _stderr
                return
            self.append_to_element('\n')
            self.history.append(currentLine)
            self.current = len(self.history)
            if self._status == "main" or self._status == "3string":
                try:
                    _ = self.editor_ns['_'] = eval(currentLine, self.editor_ns)
                    self.last_output = self.editor_ns['last_output'] = context.getvalue().strip()  # noqa
                    self.write(context.getvalue())
                    self.log_response(_)
                    self.append_to_element(PROMPT)
                    self._status = "main"
                except IndentationError:
                    if(self._status == "main"):
                        self.append_to_element(PROMPT_CONT + TAB)
                    else:
                        self.append_to_element(PROMPT_CONT)
                    self._status = "block"
                except SyntaxError as msg:
                    if str(msg) == ERR_INVALID_SYNTAX or str(msg).startswith('Unbalanced bracket'):  # noqa
                        self.append_to_element(PROMPT_CONT)
                        self._status = "3string"
                    elif str(msg) == ERR_EVAL_EXPRESSION:
                        try:
                            exec(currentLine, self.editor_ns)
                            self.last_output = self.editor_ns['last_output'] = context.getvalue().strip()  # noqa
                            self.write(context.getvalue())
                            self.log_response()
                        except:
                            self.process_error()
                        self.append_to_element(PROMPT)
                        self._status = "main"
                    elif str(msg) == 'decorator expects function':
                        self.append_to_element(PROMPT_CONT)
                        self._status = "block"
                    else:
                        self.process_error()
                        self.append_to_element(PROMPT)
                        self._status = "main"
                except:
                    self.process_error()
                    self.append_to_element(PROMPT)
                    self._status = "main"
            elif currentLine == "":  # end of block
                block = src[src.rfind('>>>') + 4:].splitlines()
                block = [block[0]] + [b[4:] for b in block[1:]]
                block_src = '\n'.join(block)
                # status must be set before executing code in globals()
                self._status = "main"
                try:
                    exec(block_src, self.editor_ns)
                    self.last_output = self.editor_ns['last_output'] = context.getvalue().strip()  # noqa
                    self.write(context.getvalue())
                    self.log_response()
                except:
                    self.process_error()
                self.append_to_element(PROMPT)
            else:
                self.append_to_element(PROMPT_CONT)

            self.cursorToEnd()
            self.prevent(event)

        sys.stdout = _stdout
        sys.stderr = _stderr

    def myKeyDown(self, event):
        if event.keyCode == 37:  # left arrow
            sel = self.get_col()
            if sel < 1:
                event.preventDefault()
                event.stopPropagation()
        elif event.keyCode == 36:  # line start
            window.getSelection().collapseToStart()
            event.preventDefault()
        elif event.keyCode == 38:  # up
            if self.current > 0:
                pass
                # remove current line
                # set_element_value(element_value()[:len(PROMPT)])
                # current -= 1
                # append_to_element(history[current])
            event.preventDefault()
        elif event.keyCode == 40:  # down
            if self.current < len(self.history) - 1:
                pass
            #     pos = element.selectionStart
            #     col = get_col(element)
            #     # remove current line
            #     set_element_value(element_value()[:pos - col + 4])
            #     current += 1
            #     append_to_element(history[current])
            event.preventDefault()
        elif event.keyCode == 8:  # backspace
            sel = self.get_col()
            if sel < 1:
                event.preventDefault()
                event.stopPropagation()

    def insertTextAtCursor(self, text):
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

        self.cursorToEnd()

    # http://jsfiddle.net/marinagon/1v63t05q/
    def handlePaste(self, e):
        e.preventDefault()
        try:
            text = e.clipboardData.getData("text/plain")
            doc.execCommand("insertHTML", False, text)
        except:
            pass

        try:
            text = window.clipboardData.getData("Text")
            self.insertTextAtCursor(text)
        except:
            pass

    def focus(self, event):
        self.element.focus()
        self.cursorToEnd()

    def nothing(self, event):
        self.element.blur()
        event.preventDefault()
        event.stopPropagation()

    def intro_and_prompt(self, needs_prompt=True):
        if not self.is_static:
            self.set_element_value(INTRO_MSG + "\n" + PROMPT)
        elif needs_prompt:
            self.set_element_value(PROMPT)

    def attach_events(self):
        self.refresh_button.bind('click', self.refresh)
        self.element.bind('keypress', self.myKeyPress)
        self.element.bind('keydown', self.myKeyDown)
        self.element.bind('click', self.cursorToEnd)
        self.element.bind('mouseover', self.focus)
        self.element.bind('paste', self.handlePaste)
        if self.is_static:
            self.element.bind('focus', self.nothing)


console_ids = []
# __ID_APPEND__
web_consoles = [PyWebConsole(_id) for _id in console_ids]
