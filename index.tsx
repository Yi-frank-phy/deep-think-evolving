// Get references to the DOM elements
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
// Fix: Cast userInput to HTMLInputElement to access its 'value' property, which is not present on the generic HTMLElement type.
const userInput = document.getElementById("user-input") as HTMLInputElement;

// Function to add a message to the chat log
function addMessage(sender, text) {
  if (!chatLog) {
    return;
  }

  const messageElement = document.createElement("div");
  messageElement.classList.add("message", sender);

  const paragraphElement = document.createElement("p");
  paragraphElement.textContent = text;
  messageElement.appendChild(paragraphElement);

  chatLog.appendChild(messageElement);
  // Scroll to the bottom of the chat log
  chatLog.scrollTop = chatLog.scrollHeight;
}

// Handle form submission
if (chatForm && userInput) {
  chatForm.addEventListener("submit", (event) => {
    event.preventDefault(); // Prevent page reload

    const userMessage = userInput.value.trim();
    if (userMessage) {
      // Add user's message to the log
      addMessage("user", userMessage);

      // Clear the input field
      userInput.value = "";

      // Simulate an assistant response
      setTimeout(() => {
        addMessage(
          "assistant",
          `Instruction received: "${userMessage}". Acknowledged. Standby for execution.`
        );
      }, 500);
    }
  });
}
