// JavaScript to interact with todo-backend service

//const backendURL = "http://127.0.0.1:8000";  // Replace "todo-backend-svc" with localhost for local testing

async function loadTodos() {
  // TODO: Fetch todo list from todo-backend and update #todoList
  // const res = await fetch('http://todo-backend-svc:8000/todos');  // Backend endpoint
  const res = await fetch(`${backend_api}`);  // Backend endpoint
            

  const todos = await res.json();
  const list = document.getElementById('todoList');
  list.innerHTML = '';
  todos.forEach(todo => {
    const item = document.createElement('li');
    item.textContent = todo.text;  // Assuming todo object has 'text' property
    list.appendChild(item);
  });
}

async function createTodo() {
  // TODO: Post new todo to todo-backend and refresh list
  console.log("Create todo clicked");
  const input = document.getElementById('todoInput');
  if (input.value.length === 0 || input.value.length > 140) {
    alert('Todo must be 1-140 characters long');
    return;
  }
  
  //await fetch('http://todo-backend-svc:8000/todos', {
  await fetch(`${backend_api}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: input.value }),
  });
  input.value = '';
  await loadTodos();
}

document.getElementById('createTodoButton').onclick = createTodo;
window.onload = loadTodos;
