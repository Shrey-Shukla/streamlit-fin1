025-05-19 12:41:12.713 Script compilation error

Traceback (most recent call last):

  File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 553, in _run_script

    code = self._script_cache.get_bytecode(script_path)

  File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_cache.py", line 72, in get_bytecode

    filebody = magic.add_magic(filebody, script_path)

  File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/magic.py", line 46, in add_magic

    tree = ast.parse(code, script_path, "exec")

  File "/usr/local/lib/python3.13/ast.py", line 54, in parse

    return compile(source, filename, mode, flags,

                   _feature_version=feature_version, optimize=optimize)

  File "/mount/src/streamlit-fin1/app.py", line 95

    response = openai_client.chat.completions.create(

    ^^^^^^^^

IndentationError: expected an indented block after 'try' statement on line 94

2025-05-19 12:41:12.716 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.

main
