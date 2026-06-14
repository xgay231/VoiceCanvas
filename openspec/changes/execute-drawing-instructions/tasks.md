## Tasks

- [x] Inspect current backend standalone drawing interpretation endpoint and align its response contract with frontend execution needs.
- [ ] Add or update frontend API flow so recognized transcript text is submitted to the standalone drawing interpretation endpoint.
- [ ] Add a controlled DrawingCanvas execution entrypoint that maps supported `create` actions to Fabric.js rectangle, circle, text, and line objects.
- [ ] Wire voice results to drawing execution and display backend messages for non-draw/error envelopes without changing the canvas.
- [ ] Add focused tests or verification coverage for successful basic creation, non-draw message handling, and unsupported actions not crashing the UI.
- [ ] Run the relevant frontend/backend validation commands and manually verify the golden path in the browser if UI execution is implemented.
