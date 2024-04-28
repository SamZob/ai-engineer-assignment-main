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
            const improvedCodeOutput = document.getElementById("improved-code-output");
            improvedCodeOutput.textContent = snippet.improved_code || 'No improvements yet.';
            document.getElementById("test-output").textContent = snippet.tests || 'No generated tests yet.';
            document.getElementById("improved-tests-output").textContent = snippet.improved_tests || 'No improved tests yet.'
            document.getElementById("test-output").textContent = snippet.tests || 'No generated tests yet.'
            // document.getElementById("test-results").textContent = snippet.test_results.results || 'No Tests run yet.'

            // Highlight the selected snippet in the list
            const snippets = document.querySelectorAll("#snippets li");
            snippets.forEach(snippet => {
                if (snippet.querySelector('a').getAttribute('onclick').includes(id)) {
                    snippet.querySelector('button').style.display = 'none'; // Hide delete button
                } else {
                    snippet.querySelector('button').style.display = 'block'; // Show delete button for other snippets
                }
            });
        })
        .catch(error => {
            console.error('Error fetching snippet:', error);
            alert('Failed to load snippet details.');
        });
}


function removeMarkdownCodeTags(text) {
    // Regex to remove ``` followed by any word characters (like ```python)
    const regex = /```[a-zA-Z]+/g;
    // Replace these tags with an empty string
    return text.replace(regex, '').replace(/```/g, ''); // also remove closing ```
}


async function generateCode(snippetId, description) {
    const loadingMessage = document.getElementById("code-output");
    loadingMessage.innerText = 'Generating code...';  // Display loading message

    const formData = new FormData();
    formData.append('description', description);
    const response = await fetch(`/generate-code/${snippetId}`, { method: 'POST', body: formData });
    if (response.ok) {
        const snippet = await response.json();
        // Clean the code received from Markdown code block tags
        const cleanCode = removeMarkdownCodeTags(snippet.code);
        document.getElementById("code-output").innerText = cleanCode;
        document.getElementById("generate-tests-btn").disabled = false;
    } else {
        console.error('Failed to generate code:', response.statusText);
        alert('Failed to generate code.');
    }
}



async function improveCode(snippetId, feedback) {
    const loadingMessage = document.getElementById("improved-code-output");
    loadingMessage.innerText = 'Improving code...';  // Display loading message

    const formData = new FormData();
    formData.append('feedback', feedback);
    const response = await fetch(`/snippets/${snippetId}/improve-code/`, {
        method: 'POST',
        body: formData
    });
    if (response.ok) {
        const snippet = await response.json();
        // Clean the improved code from Markdown code block tags
        const cleanCode = removeMarkdownCodeTags(snippet.code);
        document.getElementById("improved-code-output").innerText = cleanCode;
        document.getElementById("improve-code-btn").disabled = false;
    } else {
        console.error('Failed to improve code:', response.statusText);
        alert('Failed to improve code.');
    }
}

    

async function generateTests(snippetId) {
    const loadingMessage = document.getElementById("test-output");
    loadingMessage.innerText = 'Generating test cases...';  // Display loading message
    
    const response = await fetch(`/snippets/${snippetId}/generate-tests/`, { method: 'POST'});
    const snippet = await response.json();
    document.getElementById("test-output").innerText = snippet.tests;
    document.getElementById("generate-tests-btn").disabled = false;
}

async function improveTests(snippetId, feedback) {
    const loadingMessage = document.getElementById("improved-tests-output");
    loadingMessage.innerText = 'Improving test cases...';  // Display loading message

    const formData = new FormData();
    formData.append('feedback', feedback);
    const response = await fetch(`/snippets/${snippetId}/improve-tests/`, { method: 'POST', body: formData });
    const snippet = await response.json();
    document.getElementById("improved-tests-output").innerText = snippet.tests;
    document.getElementById("improve-tests-btn").disabled = false;
}


async function runTests(snippetId) {
    // First, retrieve the snippet details to check the language
    const snippetResponse = await fetch(`/snippets/${snippetId}`);
    if (!snippetResponse.ok) {
        alert('Failed to retrieve snippet details.');
        return;
    }
    const snippet = await snippetResponse.json();

    // Check if the language of the snippet is Python
    if (snippet.language !== 'Python') {
        alert('Testing is only supported for Python code.');
        return; // Exit the function if the language is not Python
    }

    // Proceed with running the tests if the language is Python
    const response = await fetch(`/snippets/${snippetId}/test/`, { method: 'POST' });
    const result = await response.json();
    const testResultDiv = document.getElementById("test-result");

    if (response.ok) {
        testResultDiv.className = result.message === "Tests passed" ? "bg-green-300 p-4 rounded mb-4" : "bg-red-300 p-4 rounded mb-4";
        testResultDiv.innerText = result.output;
    } else {
        testResultDiv.className = "bg-red-300 p-4 rounded mb-4";
        testResultDiv.innerText = 'Failed to run tests due to server error. Please try again.';
    }
}


async function deleteSnippet(snippetId) {
    const response = await fetch(`/snippets/${snippetId}`, { method: 'DELETE' });
    const result = await response.json();
    console.log(result.message); // Optionally handle this message in UI
    listSnippets(); // Refresh the list after deletion
}
