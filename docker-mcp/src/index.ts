import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import Docker from "dockerode";
import { z } from "zod";

const docker = new Docker();

// Create an MCP server
const server = new McpServer({
    name: "Docker MCP Server",
    version: "1.0.0",
});

// Tool: List Containers
server.tool(
    "docker_list_containers",
    {
        all: z.boolean().optional().describe("Show all containers (default shows just running)"),
    },
    async ({ all }) => {
        try {
            const containers = await docker.listContainers({ all: all ?? false });
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(containers, null, 2),
                    },
                ],
            };
        } catch (error: any) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error listing containers: ${error.message}`,
                    },
                ],
                isError: true,
            };
        }
    }
);

// Tool: Start Container
server.tool(
    "docker_start_container",
    {
        containerId: z.string().describe("ID or name of the container to start"),
    },
    async ({ containerId }) => {
        try {
            const container = docker.getContainer(containerId);
            await container.start();
            return {
                content: [
                    {
                        type: "text",
                        text: `Container ${containerId} started successfully.`,
                    },
                ],
            };
        } catch (error: any) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error starting container ${containerId}: ${error.message}`,
                    },
                ],
                isError: true,
            };
        }
    }
);

// Tool: Stop Container
server.tool(
    "docker_stop_container",
    {
        containerId: z.string().describe("ID or name of the container to stop"),
    },
    async ({ containerId }) => {
        try {
            const container = docker.getContainer(containerId);
            await container.stop();
            return {
                content: [
                    {
                        type: "text",
                        text: `Container ${containerId} stopped successfully.`,
                    },
                ],
            };
        } catch (error: any) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error stopping container ${containerId}: ${error.message}`,
                    },
                ],
                isError: true,
            };
        }
    }
);

// Tool: Get Container Logs
server.tool(
    "docker_logs",
    {
        containerId: z.string().describe("ID or name of the container"),
        tail: z.number().optional().describe("Number of lines to show from the end of the logs"),
    },
    async ({ containerId, tail }) => {
        try {
            const container = docker.getContainer(containerId);
            const logs = await container.logs({
                stdout: true,
                stderr: true,
                tail: tail || 100,
            });
            return {
                content: [
                    {
                        type: "text",
                        text: logs.toString(),
                    },
                ],
            };
        } catch (error: any) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error fetching logs for container ${containerId}: ${error.message}`,
                    },
                ],
                isError: true,
            };
        }
    }
);

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Docker MCP Server running on stdio");
}

main().catch((error) => {
    console.error("Fatal error in main():", error);
    process.exit(1);
});
