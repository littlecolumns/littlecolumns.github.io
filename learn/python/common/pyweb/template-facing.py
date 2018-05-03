import sys
import time
import traceback
import dis
import json
from io import StringIO

from browser import document as doc, window, alert, console

def to_str(xx):
    return str(xx)

class PyTest:

    def __init__(self, data, namespace, root):
        self.desc = data['desc']
        self.assertions = data['assertions']

        if 'variables' in data:
            self.variables = data['variables']
        elif 'variables' in root:
            self.variables = root['variables']
        else:
            self.variables = {}

        if 'basis' in data:
            self.basis = data['basis']
        if 'basis' in root:
            self.basis = root['basis']
        else:
            self.basis = ''

        if 'input' in data:
            self.input = data['input']
        elif 'input' in root:
            self.input = root['input']
        else:
            self.input = ''

        if 'seed' in data:
            self.seed = data['seed']
        elif 'seed' in root:
            self.seed = root['seed']
        else:
            self.seed = 1

        self.result = None
        self.ns = namespace

    def code(self):
        _code = """
            import random
            random.seed({seed})

            input = lambda prompt: '{input}'

            exec(injected_src)""".format(seed=self.seed, input=self.input).replace("            ","")
        return _code


    def check(self, assertion):
        assertion_type = assertion[0]
        data = assertion[1]
        if assertion_type == "match" :
            return data in self.result
        elif assertion_type == "no_match":
            return data not in self.result
        else:
            console.log("Don't know assertion type", assertion_type)
        return False

    def inject_src(self):
        pieces = self.ns['src'].split("\n")
        for name, value in self.variables.items():
            for i, piece in enumerate(pieces):
                if "{} =".format(name) in piece:
                    pieces[i] = "{} = {}".format(name, value)
        self.ns['injected_src'] = "\n".join(pieces)

    def passes(self):
        if self.result is None:
            self.run()

        passes = False
        self.failures = [assertion for assertion in self.assertions if not self.check(assertion)]
        return len(self.failures) == 0

    def test_basis(self):
        if self.basis is not None:
            return self.basis.format(input=self.input) + ""
        else:
            return ''

    def error_message(self, failure):
        assertion_type = failure[0]
        data = failure[1]

        if assertion_type == "match":
            return "Expected to see **{expected}**, but didn't see it".format(input=self.input, expected=data)
        elif assertion_type == "no_match":
            return "Saw **{expected}** when it wasn't expected".format(input=self.input, expected=data)
        else:
            console.log("Don't know test type", assertion_type)

    def error_messages(self):
        return [self.error_message(failure) for failure in self.failures]

    def run(self):
        try:
            self.inject_src()
            
            context = StringIO()
            _stdout = sys.stdout
            _stderr = sys.stderr
            sys.stdout = context
            sys.stderr = context

            exec(self.code(), self.ns)

        except:
            self.result = context.getvalue()
            console.log("Error occurred inside test", traceback.format_exc())
        finally:
            self.result = context.getvalue()
            sys.stdout = _stdout
            sys.stderr = _stderr

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
        # console.log("[event]", _type, data)
        event = None
        try:
            event = window.CustomEvent.new(_type, { 'detail': data })
        except:
            # IE
            event = doc.createEvent('CustomEvent')
            event.initCustomEvent(_type, True, True, data)

        self.element.dispatchEvent(event)

    def test_solution(self):
        try:
            test = self.element.test.replace("\\n","\n")
            self.editor_ns['test'] = test.strip()

            if self.last_output and (test.strip() == self.last_output):
                self.send_event('success')
                return True
        except:
            # console.log("Failed out of comparing last value")
            pass

        # if eval("test == last_output", self.editor_ns):
        #     self.send_event('success')
        #     return True
        try:
            equals = eval(test, self.editor_ns)
            if type(equals) == bool and equals:
                self.send_event('success')
                return True
        except:
            # console.log("eval gave exception")
            pass

        try:
            equals = eval(test, self.editor_ns)
            if type(equals) == bool and equals:
                self.send_event('success')
                return True
        except:
            # console.log("eval gave exception")
            pass

        try:
            success = True
            # console.log("Loading tests")
            test_data = json.loads(test)

            self.send_event('testingstart')

            for i, test in enumerate(test_data['tests']):
                py_test = PyTest(test, self.editor_ns, root=test_data)
                if py_test.passes():
                    self.send_event('testresult', {
                        'success': True,
                        'basis': py_test.test_basis(),
                        'desc': py_test.desc
                    })
                else:
                    self.send_event('testresult', {
                        'success': False,
                        'desc': py_test.desc,
                        'basis': py_test.test_basis(),
                        'errors': py_test.error_messages()
                    })
                    success = False
            if success:
                self.send_event('success')
        except:
            pass
            # console.log("Error occurred outside test", traceback.format_exc())
        finally:
            return success

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
