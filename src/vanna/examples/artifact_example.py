#!/usr/bin/env python3
"""
Example demonstrating the artifact system in Vanna Agents.

This script shows how agents can create interactive artifacts that can be
rendered externally by developers listening for the 'artifact-opened' event.
"""

import asyncio
from typing import AsyncGenerator, Optional

from vanna import Agent, UiComponent, User, AgentConfig
from vanna.core.rich_components import ArtifactComponent
from vanna.integrations.anthropic.mock import MockLlmService
from vanna.core.interfaces import Agent, LlmService


class ArtifactDemoAgent(Agent):
    """Demo agent that creates various types of artifacts."""

    def __init__(self, llm_service: Optional[LlmService] = None) -> None:
        if llm_service is None:
            llm_service = MockLlmService("I'll help you create interactive artifacts! Try asking me to create a chart, dashboard, or interactive HTML widget.")
        super().__init__(
            llm_service=llm_service,
            config=AgentConfig(
                stream_responses=True,
                include_thinking_indicators=True,
            )
        )

    async def send_message(self, user: User, message: str, *, conversation_id: Optional[str] = None) -> AsyncGenerator[UiComponent, None]:
        """Handle user messages and create appropriate artifacts."""
        # First send the normal response
        async for component in super().send_message(user, message, conversation_id=conversation_id):
            yield component

        # Then create artifacts based on message content
        message_lower = message.lower()

        if any(word in message_lower for word in ['chart', 'graph', 'visualization', 'd3']):
            async for component in self.create_d3_visualization():
                yield component
        elif any(word in message_lower for word in ['dashboard', 'analytics', 'metrics']):
            async for component in self.create_dashboard_artifact():
                yield component
        elif any(word in message_lower for word in ['html', 'interactive', 'widget', 'demo']):
            async for component in self.create_html_artifact():
                yield component

    async def create_html_artifact(self) -> AsyncGenerator[UiComponent, None]:
        """Create a simple HTML artifact."""
        html_content = """
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #333;">Interactive HTML Artifact</h2>
            <p>This is a simple HTML artifact that can be opened externally.</p>
            <button onclick="alert('Hello from the artifact!')">Click me!</button>
            <div style="margin-top: 20px;">
                <input type="text" placeholder="Type something..." id="textInput">
                <button onclick="document.getElementById('output').textContent = document.getElementById('textInput').value">
                    Update Text
                </button>
            </div>
            <div id="output" style="margin-top: 10px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
                Output will appear here...
            </div>
        </div>
        """

        artifact = ArtifactComponent.create_html(
            content=html_content,
            title="Interactive HTML Demo",
            description="A simple HTML artifact with interactive elements"
        )

        yield UiComponent(rich_component=artifact)

    async def create_d3_visualization(self) -> AsyncGenerator[UiComponent, None]:
        """Create a D3.js visualization artifact."""
        d3_content = """
        <div id="chart" style="width: 100%; height: 400px;"></div>
        <script>
            // Sample data
            const data = [
                {name: 'A', value: 30},
                {name: 'B', value: 80},
                {name: 'C', value: 45},
                {name: 'D', value: 60},
                {name: 'E', value: 20},
                {name: 'F', value: 90}
            ];

            // Set up dimensions
            const margin = {top: 20, right: 30, bottom: 40, left: 40};
            const width = 800 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;

            // Create SVG
            const svg = d3.select("#chart")
                .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);

            // Create scales
            const xScale = d3.scaleBand()
                .domain(data.map(d => d.name))
                .range([0, width])
                .padding(0.1);

            const yScale = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.value)])
                .range([height, 0]);

            // Create bars
            svg.selectAll(".bar")
                .data(data)
                .enter().append("rect")
                .attr("class", "bar")
                .attr("x", d => xScale(d.name))
                .attr("width", xScale.bandwidth())
                .attr("y", d => yScale(d.value))
                .attr("height", d => height - yScale(d.value))
                .attr("fill", "#4CAF50")
                .on("mouseover", function(event, d) {
                    d3.select(this).attr("fill", "#45a049");
                })
                .on("mouseout", function(event, d) {
                    d3.select(this).attr("fill", "#4CAF50");
                });

            // Add axes
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(xScale));

            svg.append("g")
                .call(d3.axisLeft(yScale));
        </script>
        """

        artifact = ArtifactComponent.create_d3(
            content=d3_content,
            title="D3.js Bar Chart",
            description="An interactive bar chart built with D3.js"
        )

        yield UiComponent(rich_component=artifact)

    async def create_dashboard_artifact(self) -> AsyncGenerator[UiComponent, None]:
        """Create a dashboard-style artifact."""
        dashboard_content = """
        <div style="padding: 20px; font-family: Arial, sans-serif; background: #f5f5f5; min-height: 100vh;">
            <h1 style="color: #333; margin-bottom: 30px;">Analytics Dashboard</h1>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div class="metric-card" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666;">Total Users</h3>
                    <p style="font-size: 2em; font-weight: bold; color: #333; margin: 10px 0;">12,456</p>
                    <span style="color: #4CAF50;">↗ +5.2%</span>
                </div>

                <div class="metric-card" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666;">Revenue</h3>
                    <p style="font-size: 2em; font-weight: bold; color: #333; margin: 10px 0;">$89,432</p>
                    <span style="color: #4CAF50;">↗ +12.3%</span>
                </div>

                <div class="metric-card" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #666;">Conversion Rate</h3>
                    <p style="font-size: 2em; font-weight: bold; color: #333; margin: 10px 0;">3.4%</p>
                    <span style="color: #f44336;">↘ -0.8%</span>
                </div>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0; color: #333;">Quick Actions</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="alert('Export feature coming soon!')"
                            style="padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Export Data
                    </button>
                    <button onclick="alert('Refresh complete!')"
                            style="padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Refresh
                    </button>
                    <button onclick="alert('Settings panel opened!')"
                            style="padding: 10px 20px; background: #FF9800; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Settings
                    </button>
                </div>
            </div>
        </div>
        """

        artifact = ArtifactComponent(
            content=dashboard_content,
            artifact_type="dashboard",
            title="Analytics Dashboard",
            description="A sample analytics dashboard with metrics and controls",
            external_renderable=True,
            fullscreen_capable=True
        )

        yield UiComponent(rich_component=artifact)


def create_demo_agent() -> ArtifactDemoAgent:
    """Create a demo agent for REPL and server usage.

    Returns:
        Configured ArtifactDemoAgent instance
    """
    return ArtifactDemoAgent()


async def main() -> None:
    """Main demo function."""
    print("🎨 Artifact Demo Agent")
    print("This demo shows how to create different types of artifacts.")
    print("In a real web application, developers can listen for 'artifact-opened' events.")
    print()

    demo_agent = create_demo_agent()
    user = User(id="demo_user", username="artifact_demo")

    # Demo 1: HTML Artifact
    print("1. Creating HTML Artifact...")
    async for component in demo_agent.create_html_artifact():
        artifact = component.rich_component
        if isinstance(artifact, ArtifactComponent):
            print(f"   ✓ Created HTML artifact: {artifact.title}")
            print(f"   ✓ Artifact ID: {artifact.artifact_id}")
            print(f"   ✓ Type: {artifact.artifact_type}")
            print(f"   ✓ External renderable: {artifact.external_renderable}")
        print()

    # Demo 2: D3 Visualization
    print("2. Creating D3.js Visualization...")
    async for component in demo_agent.create_d3_visualization():
        artifact = component.rich_component
        if isinstance(artifact, ArtifactComponent):
            print(f"   ✓ Created D3 artifact: {artifact.title}")
            print(f"   ✓ Dependencies: {artifact.dependencies}")
            print(f"   ✓ Standalone HTML available via get_standalone_html()")
        print()

    # Demo 3: Dashboard
    print("3. Creating Dashboard Artifact...")
    async for component in demo_agent.create_dashboard_artifact():
        artifact = component.rich_component
        if isinstance(artifact, ArtifactComponent):
            print(f"   ✓ Created dashboard artifact: {artifact.title}")
            print(f"   ✓ Fullscreen capable: {artifact.fullscreen_capable}")
        print()

    print("🚀 Web Integration Example:")
    print("""
    In your web application, listen for the 'artifact-opened' event:

    document.querySelector('vanna-chat').addEventListener('artifact-opened', (event) => {
        const { artifactId, content, type, trigger } = event.detail;

        if (trigger === 'created' && type === 'dashboard') {
            // Auto-open dashboards in external window
            const newWindow = window.open('', '_blank');
            newWindow.document.write(event.detail.getStandaloneHTML());
            newWindow.document.close();

            // Prevent default rendering in chat
            event.detail.preventDefault();
        }
    });
    """)


if __name__ == "__main__":
    asyncio.run(main())