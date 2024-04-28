document.addEventListener("DOMContentLoaded", function() {
    const createSnippetBtn = document.getElementById("create-snippet-btn");
    createSnippetBtn.addEventListener("click", createSnippet);
    const generateCodeBtn = document.getElementById("generate-code-btn");
    const descriptionTextarea = document.getElementById("description-textarea");
    const feedbackInput = document.getElementById("feedback-input");
    const improveCodeBtn = document.getElementById("improve-code-btn");
    const generateTestsBtn = document.getElementById("generate-tests-btn");
    const feedbackTestInput = document.getElementById("feedback-test-input");
    const improveTestsBtn = document.getElementById("improve-tests-btn");
    const runTestsBtn = document.getElementById("run-tests-btn");

    listSnippets(); // Initial call to populate the list of snippets

    generateCodeBtn.addEventListener("click", function() {
        generateCode(currentSnippetId, descriptionTextarea.value);
    });

    improveCodeBtn.addEventListener("click", function() {
        const feedback = document.getElementById("feedback-input").value;
        improveCode(currentSnippetId, feedback);
    });

    generateTestsBtn.addEventListener("click", function() {
        generateTests(currentSnippetId);
    });

    improveTestsBtn.addEventListener("click", function() {
        improveTests(currentSnippetId, feedbackTestInput.value);
    });

    runTestsBtn.addEventListener("click", function() {
        runTests(currentSnippetId);
    });
});

let currentSnippetId = null; // Currently selected snippet ID

async function createSnippet() {
    const response = await fetch('/create-snippet/', { method: 'POST' });
    const snippet = await response.json();
    currentSnippetId = snippet.id; // Set the current snippet ID
    document.getElementById("generate-code-btn").disabled = false;
    listSnippets(); // Update the snippet list
}

async function listSnippets() {
    const response = await fetch('/snippets/');
    const snippets = await response.json();
    const snippetList = document.getElementById("snippets");
    snippetList.innerHTML = ''; // Clear existing list
    snippets.forEach(snippet => {
        const li = document.createElement("li");
        li.className = "flex justify-between mb-4";
        li.innerHTML = `
            <a class="w-full block p-2 bg-gray-300 rounded" href="#" onclick="selectSnippet('${snippet.id}')">
                ${snippet.title || 'New Snippet'} | ${snippet.language || 'Pending'}
            </a>
            <button class="bg-red-500 text-white px-2 py-1 rounded" onclick="deleteSnippet('${snippet.id}')">
                Delete
            </button>
        `;
        snippetList.appendChild(li);
    });
}

function selectSnippet(id) {
    currentSnippetId = id; // Set current snippet ID globally
    
    // Enable buttons
    document.getElementById("generate-code-btn").disabled = false;
    document.getElementById("improve-code-btn").disabled = false;
    document.getElementById("generate-tests-btn").disabled = false;
    document.getElementById("improve-tests-btn").disabled = false;
    document.getElementById("run-tests-btn").disabled = false;

    // Fetch snippet details from the server
    fetch(`/snippets/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Snippet not found');
            }
            return response.json();
        })
        .then(snippet => {
            // Display snippet details
            document.getElementById("description-textarea").value = snippet.description || '';
            document.getElementById("code-output").textContent = snippet.code || 'No code generated yet.';
            const improvedCodeOutput = document.getElementById("improved-code-output"); // Make sure you have this element in your HTML
            improvedCodeOutput.textContent = snippet.improved_code || 'No improvements yet.';
            document.getElementById("test-output").textContent = snippet.tests || 'No generated tests yet.';
            document.getElementById("improved-tests-output").textContent = snippet.improved_tests || 'No improved tests yet.'
            document.getElementById("test-output").textContent = snippet.tests || 'No generated tests yet.'
            document.getElementById("test-result").textContent = snippet.tests_results || 'No Tests run yet.'

        })
        .catch(error => {
            console.error('Error fetching snippet:', error);
            alert('Failed to load snippet details.');
        });
}


async function generateCode(snippetId, description) {
    const formData = new FormData();
    formData.append('description', description);
    const response = await fetch(`/generate-code/${snippetId}`, { method: 'POST', body: formData });
    const snippet = await response.json();
    document.getElementById("code-output").innerText = snippet.code;
    document.getElementById("generate-tests-btn").disabled = false;
}


async function improveCode(snippetId, feedback) {
    const formData = new FormData();
    formData.append('feedback', feedback);
    const response = await fetch(`/snippets/${snippetId}/improve-code/`, {
        method: 'POST',
        body: formData
    });
    const snippet = await response.json();
    if (response.ok) {
        document.getElementById("improved-code-output").innerText = snippet.improved_code;
        alert("Code improved successfully.");
    } else {
        alert("Failed to improve code: " + snippet.detail);
    }
}


async function generateTests(snippetId) {
    const response = await fetch(`/snippets/${snippetId}/generate-tests/`, { method: 'POST'});
    const snippet = await response.json();
    document.getElementById("test-output").innerText = snippet.tests;
}

async function improveTests(snippetId, feedback) {
    const formData = new FormData();
    formData.append('feedback', feedback);
    const response = await fetch(`/snippets/${snippetId}/improve-tests/`, { method: 'POST', body: formData });
    const snippet = await response.json();
    document.getElementById("improved-tests-output").innerText = snippet.improved_tests;
}

async function runTests(snippetId) {
    const response = await fetch(`/snippets/${snippetId}/test/`, { method: 'POST' });
    const result = await response.json();
    const testResultDiv = document.getElementById("test-result");
    if (result.message === "Tests passed") {
        testResultDiv.className = "bg-green-300 p-4 rounded mb-4";
    } else {
        testResultDiv.className = "bg-red-300 p-4 rounded mb-4";
    }
    document.getElementById("test-output").innerText =  result.results
    testResultDiv.innerText = result.results;
}

async function deleteSnippet(snippetId) {
    const response = await fetch(`/snippets/${snippetId}`, { method: 'DELETE' });
    const result = await response.json();
    console.log(result.message); // Optionally handle this message in UI
    listSnippets(); // Refresh the list after deletion
}