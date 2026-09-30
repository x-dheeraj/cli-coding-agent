let todos = [];

function addTodo() {
	const todoInput = document.getElementById("todo-input").value;
	if (todoInput.trim() !== "") {
		const todo = {
			text: todoInput,
			completed: false
		}
		todos.push(todo);
		document.getElementById("todo-input").value = "";
		renderTodos();
	}
}

function renderTodos() {
	const todoList = document.getElementById("todo-list");
	todoList.innerHTML = "";
	todos.forEach(todo => {
		const li = document.createElement("li");
		li.textContent = todo.text;
		if (todo.completed) {
			li.className = "completed";
		}
		li.addEventListener("click", () => toggleCompleted(todo));
		todoList.appendChild(li);
	});
}

function toggleCompleted(todo) {
	todo.completed = !todo.completed;
	renderTodos();
}