

# Run basic tests
todo-backend [main]$ pytest -s --verbose
=========================================================================================================== test session starts ============================================================================================================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0 -- /home/arkane/.venvs/awscli-env/bin/python3
cachedir: .pytest_cache
rootdir: /home/arkane/workspace/devops-kubernetes/the_project/todo-backend
configfile: pytest.ini
plugins: asyncio-1.3.0, anyio-4.11.0, freezegun-0.4.2, mock-3.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2 items

tests/test_app.py::test_get_todos_empty PASSED
tests/test_app.py::test_post_todo_and_get PASSED

============================================================================================================ 2 passed in 2.30s =============================================================================================================
todo-backend [main]$