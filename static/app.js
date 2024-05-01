// Event listener to ensure DOM content is loaded before scripts run
document.addEventListener("DOMContentLoaded", function() {
    // Button elements and other controls
    const createSnippetBtn = document.getElementById("create-snippet-btn");
    createSnippetBtn.addEventListener("click", createSnippet);
    const generateCodeBtn = document.getElementById("generate-code-btn");
    const descriptionTextarea = document.getElementById("description-textarea");
    const improveCodeBtn = document.getElementById("improve-code-btn");
    const generateTestsBtn = document.getElementById("generate-tests-btn");
    const feedbackTestInput = document.getElementById("feedback-test-input");
    const improveTestsBtn = document.getElementById("improve-tests-btn");
    const runTestsBtn = document.getElementById("run-tests-btn");
    const regenerateCodeBtn = document.getElementById("regenerate-code-btn");

    // Initial fetch and display of snippets
    listSnippets();

    // Event listeners for buttons that initiate API calls
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

    regenerateCodeBtn.addEventListener("click", function() {
        regenerateCode(currentSnippetId);
    });
});

// Variable to keep track of the currently selected snippet ID
let currentSnippetId = null;

// Function to create a new snippet via API and update UI
async function createSnippet() {
    const response = await fetch('/create-snippet/', { method: 'POST' });
    const snippet = await response.json();
    currentSnippetId = snippet.id; // Set the current snippet ID
    document.getElementById("generate-code-btn").disabled = false;
    listSnippets(); // Refresh the list of snippets
}

// Function to display all snippets in the UI
async function listSnippets() {
    const response = await fetch('/snippets/');
    const snippets = await response.json();
    const snippetList = document.getElementById("snippets");
    snippetList.innerHTML = ''; // Clear existing snippet list
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

// Function to extract only the content inside Markdown code blocks
function extractCodeBlocks(text) {
    // Regex to match complete code blocks including language specifier and enclosed content
    const regex = /```[a-zA-Z]+\s*\n([\s\S]*?)```/g;
    const regex2 = /```[a-zA-Z]+\s*\n([\s\S]*?)/g;
    let matches, codeBlocks = [];

    // Iterate over all regex matches and collect the contents of the code blocks
    while ((matches = regex.exec(text)) !== null || (matches = regex2.exec(text)) !== null) {
        // Push each found code block's content to an array
        codeBlocks.push(matches[1]);
    }

    // Combine all extracted code blocks into a single string separated by new lines
    return codeBlocks.join('\n');
}

// Function to handle selecting a snippet, updating UI and fetching details
function selectSnippet(id) {
    currentSnippetId = id; // Update current snippet ID
    // Reset display areas to default messages
    document.getElementById("code-output").textContent = 'No code generated yet.';
    document.getElementById("improved-code-output").textContent = 'No improvements yet.';
    document.getElementById("test-output").textContent = 'No generated tests yet.';
    document.getElementById("improved-tests-output").textContent = 'No improved tests yet.';
    document.getElementById("test-result").textContent = '';
    document.getElementById("regeneration-result").textContent = '';
    document.getElementById("regenerate-code-result").textContent = ''
    document.getElementById("test-result").className = '';
    document.getElementById("regeneration-result").className = '';

    // Enable all buttons now that a snippet is selected
    document.getElementById("generate-code-btn").disabled = false;
    document.getElementById("improve-code-btn").disabled = false;
    document.getElementById("generate-tests-btn").disabled = false;
    document.getElementById("improve-tests-btn").disabled = false;
    document.getElementById("run-tests-btn").disabled = false;
    document.getElementById("regenerate-code-btn").disabled = false;

    // Fetch detailed information for the selected snippet
    fetch(`/snippets/${id}`)
        .then(response => {
            if (!response.ok) throw new Error('Snippet not found');
            return response.json();
        })
        .then(snippet => {
            // Update display areas with snippet details
            document.getElementById("description-textarea").value = snippet.description || '';
            document.getElementById("code-output").textContent = extractCodeBlocks(snippet.code) || 'No code generated yet.';
            document.getElementById("improved-code-output").textContent = extractCodeBlocks(snippet.improved_code) || 'No improvements yet.';
            document.getElementById("test-output").textContent = snippet.tests || 'No generated tests yet.';
            document.getElementById("improved-tests-output").textContent = snippet.improved_tests || 'No improved tests yet.';

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


// Function to generate code for a snippet based on a description
async function generateCode(snippetId, description) {
    // Display a loading message in the code output area during processing
    const loadingMessage = document.getElementById("code-output");
    loadingMessage.innerText = 'Generating code...';

    // Prepare the request data
    const formData = new FormData();
    formData.append('description', description);

    // Make a POST request to generate code for the given snippet
    const response = await fetch(`/generate-code/${snippetId}`, { method: 'POST', body: formData });
    if (response.ok) {
        const snippet = await response.json();
        // Extract and clean code from the snippet, removing Markdown syntax
        const cleanCode = extractCodeBlocks(snippet.code);
        document.getElementById("code-output").innerText = cleanCode;
    } else {
        // Log errors and alert the user if code generation fails
        console.error('Failed to generate code:', response.statusText);
        alert('Failed to generate code.');
    }
}

// Function to improve code based on user feedback
async function improveCode(snippetId, feedback) {
    // Display a loading message in the improved code output area during processing
    const loadingMessage = document.getElementById("improved-code-output");
    loadingMessage.innerText = 'Improving code...';

    // Prepare the request data
    const formData = new FormData();
    formData.append('feedback', feedback);

    // Make a POST request to improve the code for the given snippet
    const response = await fetch(`/snippets/${snippetId}/improve-code/`, { method: 'POST', body: formData });
    if (response.ok) {
        const snippet = await response.json();
        // Extract and clean the improved code, removing Markdown syntax
        const cleanCode = extractCodeBlocks(snippet.code);
        document.getElementById("improved-code-output").innerText = cleanCode;
    } else {
        // Log errors and alert the user if code improvement fails
        console.error('Failed to improve code:', response.statusText);
        alert('Failed to improve code.');
    }
}

// Function to generate tests for a snippet's code
async function generateTests(snippetId) {
    // Display a loading message in the test output area during processing
    const loadingMessage = document.getElementById("test-output");
    loadingMessage.innerText = 'Generating test cases...';

    // Make a POST request to generate tests for the given snippet
    const response = await fetch(`/snippets/${snippetId}/generate-tests/`, { method: 'POST' });
    const snippet = await response.json();
    document.getElementById("test-output").innerText = snippet.tests;
    document.getElementById("generate-tests-btn").disabled = false;
}

// Function to improve test cases based on user feedback
async function improveTests(snippetId, feedback) {
    // Display a loading message in the improved tests output area during processing
    const loadingMessage = document.getElementById("improved-tests-output");
    loadingMessage.innerText = 'Improving test cases...';

    // Prepare the request data
    const formData = new FormData();
    formData.append('feedback', feedback);

    // Make a POST request to improve the test cases for the given snippet
    const response = await fetch(`/snippets/${snippetId}/improve-tests/`, { method: 'POST', body: formData });
    const snippet = await response.json();
    document.getElementById("improved-tests-output").innerText = snippet.tests;
}

// Function to run tests on a snippet's code
async function runTests(snippetId) {
    // Retrieve the snippet details to check the language before running tests
    const snippetResponse = await fetch(`/snippets/${snippetId}`);
    if (!snippetResponse.ok) {
        alert('Failed to retrieve snippet details.');
        return;
    }
    const snippet = await snippetResponse.json();

    // Only support testing for Python code
    if (snippet.language !== 'Python') {
        alert('Testing is only supported for Python code.');
        return;
    }

    // Make a POST request to run tests on the given snippet
    const response = await fetch(`/snippets/${snippetId}/test/`, { method: 'POST' });
    const result = await response.json();
    const testResultDiv = document.getElementById("test-result");

    // Display the test results with appropriate styling based on success or failure
    if (response.ok) {
        testResultDiv.className = result.message === "Tests passed" ? "bg-green-300 p-4 rounded mb-4" : "bg-red-300 p-4 rounded mb-4";
        testResultDiv.innerText = result.output;
    } else {
        testResultDiv.className = "bg-red-300 p-4 rounded mb-4";
        testResultDiv.innerText = 'Failed to run tests due to server error. Please try again.';
    }
}

// Function to regenerate code for a snippet based on failed tests
async function regenerateCode(snippetId) {
    // Make a POST request to regenerate code for the given snippet
    const response = await fetch(`/snippets/${snippetId}/regenerate-code/`, { method: 'POST' });
    const resultDiv = document.getElementById("regeneration-result");
    const results = document.getElementById("regenerate-code-result")
    resultDiv.className = "p-4 rounded mb-4"; // Reset class to ensure visibility styling
    if (response.ok) {
        const result = await response.json();
        const cleanCode = extractCodeBlocks(result.code);
        results.textContent = cleanCode;
        resultDiv.textContent = 'Code regenerated successfully.';
        resultDiv.classList.add("bg-green-300"); // Add success styling
    } else {
        resultDiv.textContent = 'Failed to regenerate code. Please check the test results.';
        resultDiv.classList.add("bg-red-300"); // Add failure styling
    }
    resultDiv.classList.remove("hidden"); // Make the div visible
}

// Function to delete a snippet
async function deleteSnippet(snippetId) {
    // Make a DELETE request to remove the specified snippet
    const response = await fetch(`/snippets/${snippetId}`, { method: 'DELETE' });
    const result = await response.json();
    console.log(result.message); // Log deletion message for debugging
    listSnippets(); // Refresh the list of snippets after deletion
}

