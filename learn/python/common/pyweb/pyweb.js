window.pyweb = (function() {
  let facing_template
  let facing_i = 0
  let facing_ids = []

  function createFacingElement (basis) {
    console.log("Creating a facing from", basis)
    let id = "py-facing-" + facing_i
    let editor_id = "py-facing-" + facing_i + "-editor"
    facing_i++
    facing_ids.push(id)
    
    let editor = basis.cloneNode(true)
    editor.id = editor_id

    let row = document.createElement('div')
    row.id = id
    row.classList.add('row', 'py-facing-row', 'no-gutters')
    row.setAttribute('run', basis.getAttribute('run') == 'true')
    
    let aceCol = document.createElement('div')
    aceCol.classList.add('col-lg')
    let aceHolder = document.createElement('div')
    aceHolder.classList.add('ace-holder')
    aceHolder.appendChild(editor)
    aceCol.appendChild(aceHolder)

    let button = document.createElement('a')
    button.classList.add('btn', 'btn-warning', 'btn-block', 'rounded-0', 'btn-run')
    button.innerHTML = "<span class='oi oi-play-circle'></span> Run Python code"
    aceCol.appendChild(button)

    let resultCol = document.createElement('div')
    resultCol.classList.add('col-lg')
    resultCol.classList.add('facing-result')
    let result = document.createElement('pre')
    result.classList.add('h-100', 'output')
    resultCol.appendChild(result)

    row.appendChild(aceCol)
    row.appendChild(resultCol)

    basis.parentNode.insertBefore(row, basis.nextSibling)
    basis.parentNode.removeChild(basis)

    ace.edit(editor, {
      theme: "ace/theme/tomorrow_night",
      mode: "ace/mode/python",
      fontFamily: "'Oxygen Mono', Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace",
      indentedSoftWrap: false,
      showLineNumbers: true,
      wrap: true,
      useSoftTabs: true,
      scrollPastEnd: 2,
      autoScrollEditorIntoView: true,
      // readOnly: !!editor.getAttribute('static'),
      maxLines: 30,
      minLines: 5,
      fontSize: 16,
      showGutter: true
    })
  }

  function createFacingElements (query, base) {
    if (!base) {     
      base = ""
    }
    return fetch(base + 'template-facing.py')
      .then(function (response) {
        return response.text()
      })
      .then(function (text) {
        facing_template = text

        let elements = document.querySelectorAll(query)
        for(let i = 0; i < elements.length; i++) {
          createFacingElement(elements[i])
        }
      })
      .then(function () {
        var insert_line = facing_ids.map(function (id) {
          return "facing_ids.append('" + id + "')"
        }).join("\n")
        let repl_signal = "# __ID_APPEND__"
        let code = facing_template.replace(repl_signal, insert_line)

        let script = document.createElement('script')

        script.setAttribute('type', 'text/python3')
        script.appendChild(document.createTextNode(code))
        
        document.querySelector('body').appendChild(script)
      })
  }

  let console_i = 0
  let console_template
  let console_ids = []

  function createConsoleElement (basis) {

    let element = basis.cloneNode(true)
    basis.parentNode.insertBefore(element, basis.nextSibling)
    basis.parentNode.removeChild(basis)
    
    let id = "brython-" + console_i
    let brython = document.createElement('div')
    brython.id = id
    console_ids.push(id)
    console_i++

    brython.contentEditable = true
    brython.spellcheck = false

    brython.autocomplete = false
    brython.autocorrect = false
    brython.autocapitalize = false
    brython.setAttribute('test', element.getAttribute('test'))
    brython.setAttribute('static', element.getAttribute('static'))
    if(brython.attributes['test']) {
      element.classList.add('is-incomplete')
    }
    brython.innerHTML = element.innerHTML
    brython.className = "py-console"

    element.innerHTML = ""
    element.appendChild(brython)

    brython.addEventListener('success', function(event) {
      element.classList.add('is-success')

      confetti(element, {
        angle: 60,
        spread: 50,
        startVelocity: 80,
        elementCount: 100,
        decay: 0.8
      })
    })

    brython.addEventListener('error', function(event) {
      // console.log(event)
    })

    brython.addEventListener('message', function(event) {
      // console.log(event)
    })

    element.classList.add('is-ready')
  }

  // console_template.py contains a template
  // that looks for doc['code'], we'll eventually
  // do a find-and-replace on that pointing to
  // different specific IDs
  function createConsoleElements (query, base) {
    if (!base) {
      base = ""
    }
    return fetch(base + 'template-console.py')
      .then(function (response) {
        return response.text()
      })
      .then(function (text) {
        console_template = text

        let elements = document.querySelectorAll(query)
        for(let i = 0; i < elements.length; i++) {
          createConsoleElement(elements[i])
        }
      })
      .then(function () {
        var insert_line = console_ids.map(function (id) {
          return "console_ids.append('" + id + "')"
        }).join("\n")
        let repl_signal = "# __ID_APPEND__"
        let code = console_template.replace(repl_signal, insert_line)

        let script = document.createElement('script')

        script.setAttribute('type', 'text/python3')
        script.appendChild(document.createTextNode(code))
        
        document.querySelector('body').appendChild(script)
      })
  }

  function initialize (options) {
    if (!options) {
      options = {}
    }
    Promise.all([
      createConsoleElements(options.console, options.base),
      createFacingElements(options.facing, options.base)
    ]).then(function () {
      brython(1)
    })
  }

  return {
    initialize: initialize 
  }
})()