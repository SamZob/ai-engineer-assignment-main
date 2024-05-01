# Code Snippet Generation

The application support the following programming languages:

- `Python`
- `Javascript`
- `Ruby`

For snippet description/feedback, the following languagues are supported:

- `English`
- `Japanese`

## Getting Started

 To get started, **ADD YOUR API KEY** to `start-docker-server.sh` in:

 ```bash
 docker run --rm -p 8000:8000 -e OPENAI_API_KEY=<YOUR_API_KEY> $IMAGE_NAME
 ```
 **with double quotes**
 
  Using the .env file to store the API didn't work as expected when running container (OPEN AI API endpoint doesn't recognize tha api key provided), otherwise the app works fine using python locally.

  Run the `start-docker-server.sh` to start the server and visit `http://localhost:8000` to see the project. Docker must be installed.

 ## Areas of improvement
 
 Here are different aspects that could be integrated to the application to enhance its capabilities:

 ### BackEnd

 1. **Enhanced Test Generation**:
   - Implement more sophisticated test generation methods that can understand the structure and logic of the provided code snippets. This could involve using machine learning techniques or more advanced pattern matching algorithms.
   - Provide options for the user to specify test criteria or constraints, such as input ranges, edge cases, or specific behaviors to test.

2. **Dynamic Test Execution**:
   - Develop a more flexible test execution system that can handle tests for various programming languages beyond just Python. This could involve integrating with testing frameworks specific to each language.
   - Improve error handling and reporting during test execution to provide clearer feedback on test failures, including highlighting the specific test case that failed and the reason for failure.

3. **Parallel Testing**:
   - Implement parallel test execution to improve performance, especially when running tests for multiple functions or large test suites. This could involve utilizing multiprocessing or asynchronous programming techniques.

4. **Code Coverage Analysis**:
   - Integrate code coverage analysis tools to assess the effectiveness of the tests generated. This would help identify areas of the code that are not adequately covered by the tests, guiding further test generation efforts.

5. **Feedback Loop**:
   - Establish a feedback loop where the results of test execution are analyzed to identify patterns of failures or areas where the test generation process can be improved. This feedback can then be used to refine the test generation algorithms.

6. **Optimization for Algebraic Functions**:
   - Develop specialized methods for generating and testing algebraic functions, leveraging mathematical properties and transformations to generate meaningful test cases.
   - Explore techniques such as symbolic computation or algebraic simplification to assist in generating test inputs and expected outputs for algebraic functions.

7. **Security Considerations**:
   - Implement security measures to prevent malicious code injection or unintended behaviors during test execution, especially when executing user-provided code snippets.
   - Consider sandboxing or containerization techniques to isolate test execution environments and mitigate potential security risks.

### Frontend

1. **Error Handling and Feedback**:
- Implement more robust error handling mechanisms throughout the application to provide meaningful feedback to users when actions fail.
- Display appropriate error messages in the UI when API requests fail, guiding users on how to proceed.

2. **User Experience Enhancements**:
- Improve the user interface with clearer visual cues and feedback during code generation, test execution, and other asynchronous processes.
- Consider adding loading spinners or progress indicators to indicate when actions are in progress.

3. **Snippet Management**:
- Enhance the snippet list UI with features such as pagination, sorting, or filtering to improve usability, especially when dealing with a large number of snippets.
- Allow users to edit snippet descriptions or titles directly from the UI, providing a more seamless editing experience.

4. **Code Presentation**:
- Implement syntax highlighting for code snippets displayed in the UI to improve readability and make the code more visually appealing.
- Provide options for users to toggle between different code highlighting themes to customize their viewing experience.

5. **Input Validation and Sanitization**:
- Implement input validation mechanisms to ensure that user-provided inputs are sanitized and validated before being sent to the server.
- Validate user inputs such as descriptions, feedback, or test cases to prevent potential security vulnerabilities or data corruption.




