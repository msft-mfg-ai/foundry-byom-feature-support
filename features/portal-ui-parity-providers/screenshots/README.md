# Portal-ui-parity-providers screenshots

Capture from the Foundry portal → Management center → Connections → New connection.

- `01-add-connection-provider-list.png` — Provider tile grid. Show that AzureOpenAI / OpenAI are present but ApiManagement and ModelGateway are NOT offered as tiles (the missing-provider evidence). **Re-shoot needed:** the current capture has the background "Connected resources" table visible, which leaks the real subscription ID, resource group name, and user UPN in that table — either scroll/crop so only the modal is visible, or capture on a page with no existing connections listed.
- `02-apim-v2-only-endpoint-shape.png` — If a code-created APIM connection already exists, open its edit dialog and capture the endpoint field / model list showing the v2/openai-chat-completions shape. **Re-shoot needed:** same leak as #1 (full-page "Basic configuration" screen shows subscription ID, resource group, and user UPN in the connections table) — crop to just the endpoint/model-list panel.
