/**
 * Available MCP operations
 */
export var McpOperation;
(function (McpOperation) {
    McpOperation["LIST_TOOLS"] = "tools/list";
    McpOperation["CALL_TOOL"] = "tools/call";
    McpOperation["INITIALIZE"] = "initialize";
    McpOperation["PING"] = "ping";
})(McpOperation || (McpOperation = {}));
