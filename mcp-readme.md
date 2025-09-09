# MCP Tool Development Guide

This guide provides a walkthrough for creating and integrating new tools using the Model-Context Protocol (MCP). By following these steps, you can extend the capabilities of the Gemini model, allowing it to interact with new services and APIs. We will use the existing Google Maps integration (`mcp_maps_server.ts`) as our primary example.

## Core Concepts

Before we start, let's define a few key terms:

- **MCP (Model-Context Protocol):** A protocol that enables AI models to safely and predictably call external tools and services.
- **MCP Server:** A service that exposes a set of tools. It listens for tool-call requests from a client, executes the corresponding code, and returns a result.
- **MCP Client:** The component within the main application that connects to an MCP server and makes its tools available to the Gemini model.
- **Transport:** The communication channel between the client and server. In this project, we use `InMemoryTransport`, which allows the client and server to run in the same browser session—perfect for demos.
- **Tool:** A single function that the AI model can invoke. Each tool has a unique `name`, a detailed `description` (which is critical for the AI to understand its purpose), a `schema` for its arguments, and a `handler` function that contains its logic.

---

## Steps to Create and Integrate a New Tool

Let's imagine we want to create a new tool that gets the current weather.

### Step 1: Create the MCP Server File

Create a new file for your tool server, for example, `mcp_weather_server.ts`. This keeps your tools organized and separate from the main application logic.

### Step 2: Set Up the Server Boilerplate

Inside `mcp_weather_server.ts`, add the necessary imports and create a function to initialize the server. This function will accept a `transport` and a `handler` callback to communicate with the main application's UI.

```typescript
// mcp_weather_server.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';
import { z } from 'zod';

// Define the parameters your UI handler will accept
export interface WeatherParams {
  location: string;
}

export async function startMcpWeatherServer(
  transport: Transport,
  weatherQueryHandler: (params: WeatherParams) => void,
) {
  // Create an MCP server instance
  const server = new McpServer({
    name: 'Weather Service',
    version: '1.0.0',
  });

  // Tools will be defined here...

  // Connect the server to the transport
  await server.connect(transport);
  console.log('Weather MCP server running');
}
```

### Step 3: Define Your Tool

Use the `server.tool()` method to define each function you want to expose to the Gemini model.

- **`name`**: A unique, snake_case identifier for the tool.
- **`description`**: A clear, detailed explanation of what the tool does. This is **the most important part**, as the model uses this description to decide when and how to use your tool. Be specific about what it does and what kind of input it expects.
- **`schema`**: An object defined with `zod` that specifies the arguments the tool accepts, their types, and descriptions for each.
- **`handler`**: An `async` function that receives the validated arguments and executes your tool's logic.

```typescript
// Inside startMcpWeatherServer in mcp_weather_server.ts

server.tool(
  'get_current_weather',
  'Gets the current weather for a specific city and displays it to the user.',
  // Zod schema for input validation
  {
    location: z.string().describe('The city and state, e.g., "San Francisco, CA"'),
  },
  // Handler function to execute the tool's logic
  async ({ location }) => {
    // Call the handler passed from the main app to update the UI
    weatherQueryHandler({ location });

    // Return a result to the Gemini model to confirm the action
    return {
      content: [{ type: 'text', text: `Success: Displaying the weather for ${location}` }],
    };
  },
);
```

### Step 4: Integrate the New Server into the Application

Now, let's hook up your new server in `index.tsx`.

1.  **Import your new server function.**

    ```typescript
    // in index.tsx
    import { startMcpGoogleMapServer } from './mcp_maps_server';
    import { startMcpWeatherServer } from './mcp_weather_server'; // Add this line
    ```

2.  **Create a new transport pair and client for your service.** Each MCP server needs its own client.

    ```typescript
    // in index.tsx, inside the DOMContentLoaded listener

    // --- Map Server Setup (existing code) ---
    const [mapTransportA, mapTransportB] = InMemoryTransport.createLinkedPair();
    void startMcpGoogleMapServer(mapTransportA, (params) => {
      playground.renderMapQuery(params);
    });
    const mcpMapsClient = await startClient(mapTransportB);

    // --- Weather Server Setup (new code) ---
    const [weatherTransportA, weatherTransportB] = InMemoryTransport.createLinkedPair();
    void startMcpWeatherServer(weatherTransportA, (params) => {
      // Here you would add logic to display weather info in the UI.
      // For now, we'll just log it and add a message to the chat.
      console.log(`Weather for ${params.location} was requested.`);
      playground.addMessage('assistant', `Here is the weather for ${params.location}: ☀️ 75°F`);
    });
    const mcpWeatherClient = await startClient(weatherTransportB);
    ```

3.  **Add the new tool client to the Gemini chat instance.** The `tools` array in the chat configuration can accept multiple tool sets.

    ```typescript
    // in index.tsx

    function createAiChat(mcpClients: Client[]) { // Update to accept an array of clients
      return ai.chats.create({
        model: 'gemini-2.5-flash',
        config: {
          systemInstruction: SYSTEM_INSTRUCTIONS,
          tools: mcpClients.map(client => mcpToTool(client)), // Map over clients
        },
      });
    }

    // ... later in the DOMContentLoaded listener

    // Pass an array of all your clients to the chat creation function
    const aiChat = createAiChat([mcpMapsClient, mcpWeatherClient]);
    ```

That's it! When you now ask the model a question about the weather, it will recognize your new tool from its description and use it to fulfill the request.

---

## Best Practices

- **Write Excellent Descriptions:** The model's ability to use your tool is almost entirely dependent on the quality of the `name` and `description`. Be clear, concise, and provide examples if necessary.
- **Keep Tools Atomic:** Prefer smaller, single-purpose tools over one large, complex tool. For example, `search_google_maps` and `directions_on_google_maps` are better than a single tool that does both.
- **Provide Useful Feedback:** The `return` value from your tool handler is sent back to the model. Use it to confirm that an action was taken (e.g., "Map is now centered on Paris") or to return data that the model might need for its final response.
- **Use `zod` Descriptions:** Use `.describe()` on your Zod schema properties to give the model hints about the expected format for each argument.
