"""
HTML templates for Vanna Agents servers.
"""

from typing import Optional


def get_vanna_component_script(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://unpkg.com/@vanna-ai/web-components@latest/dist/index.js"
) -> str:
    """Get the script tag for loading Vanna web components.

    Args:
        dev_mode: If True, load from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production

    Returns:
        HTML script tag for loading components
    """
    if dev_mode:
        return f'<script type="module" src="{static_path}/vanna-components.js"></script>'
    else:
        return f'<script type="module" src="{cdn_url}"></script>'


def get_index_html(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://unpkg.com/@vanna-ai/web-components@latest/dist/index.js",
    api_base_url: str = ""
) -> str:
    """Generate index HTML with configurable component loading.

    Args:
        dev_mode: If True, load components from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production components
        api_base_url: Base URL for API endpoints

    Returns:
        Complete HTML page as string
    """
    component_script = get_vanna_component_script(dev_mode, static_path, cdn_url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vanna Agents Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        vanna-chat {{
            width: 100%;
            height: 100%;
            display: block;
        }}
    </style>
    {component_script}
</head>
<body class="bg-gray-100">
    <div class="max-w-6xl mx-auto p-5">
        <!-- Header -->
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">🤖 Vanna Agents</h1>
            <p class="text-gray-600 mb-4">Interactive AI Assistant powered by Vanna Agents Framework</p>
            <a href="javascript:window.location='view-source:'+window.location.href" class="inline-flex items-center gap-2 px-4 py-2 mb-4 bg-gray-800 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
                </svg>
                View Page Source
            </a>
            <div class="bg-green-50 border border-green-400 rounded-lg p-3 text-sm text-green-800">
                🎨 <strong>Artifact Demo Mode:</strong> All artifacts will open in external windows with placeholder shown in chat.
                Open browser console to see event logs.
            </div>
        </div>

        {('    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-5 text-yellow-800 text-sm">📦 Development Mode: Loading components from local assets</div>' if dev_mode else '')}

        <!-- Login Form -->
        <div id="loginContainer" class="max-w-md mx-auto mb-10 bg-white p-8 rounded-xl shadow-lg">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-semibold text-gray-800 mb-2">Login to Continue</h2>
                <p class="text-sm text-gray-600">Enter your email to access the chat</p>
            </div>

            <div class="mb-5">
                <label for="emailInput" class="block mb-2 text-sm font-medium text-gray-700">Email Address</label>
                <input
                    type="email"
                    id="emailInput"
                    class="w-full px-4 py-3 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="your.email@example.com"
                    autocomplete="email"
                />
            </div>

            <button id="loginButton" class="w-full px-4 py-3 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition disabled:bg-gray-400 disabled:cursor-not-allowed">
                Continue
            </button>

            <div class="mt-5 p-3 bg-blue-50 border-l-4 border-blue-500 rounded text-xs text-gray-700 leading-relaxed">
                <strong>Demo Mode:</strong> This is a frontend-only authentication demo.
                Your email will be stored as a cookie and automatically sent with all API requests.
            </div>
        </div>

        <!-- Logged In Status (hidden by default) -->
        <div id="loggedInStatus" class="hidden text-center p-4 bg-green-100 border border-green-300 rounded-lg mb-5">
            Logged in as <span id="loggedInEmail" class="font-semibold text-green-800"></span>
            <br>
            <button id="logoutButton" class="mt-2 px-3 py-1.5 bg-gray-600 text-white text-xs rounded hover:bg-gray-700 transition">
                Logout
            </button>
        </div>

        <!-- Chat Container (hidden by default) -->
        <div id="chatSections" class="hidden">
            <div class="bg-white rounded-xl shadow-lg h-[600px] overflow-hidden">
                <vanna-chat
                    api-base="{api_base_url}"
                    sse-endpoint="{api_base_url}/api/vanna/v2/chat_sse"
                    ws-endpoint="{api_base_url}/api/vanna/v2/chat_websocket"
                    poll-endpoint="{api_base_url}/api/vanna/v2/chat_poll">
                </vanna-chat>
            </div>

            <div class="mt-8 p-5 bg-white rounded-lg shadow">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">API Endpoints</h3>
                <ul class="space-y-2">
                    <li class="p-2 bg-gray-50 rounded font-mono text-sm">
                        <span class="font-bold text-blue-600 mr-2">POST</span>{api_base_url}/api/vanna/v2/chat_sse - Server-Sent Events streaming
                    </li>
                    <li class="p-2 bg-gray-50 rounded font-mono text-sm">
                        <span class="font-bold text-blue-600 mr-2">WS</span>{api_base_url}/api/vanna/v2/chat_websocket - WebSocket real-time chat
                    </li>
                    <li class="p-2 bg-gray-50 rounded font-mono text-sm">
                        <span class="font-bold text-blue-600 mr-2">POST</span>{api_base_url}/api/vanna/v2/chat_poll - Request/response polling
                    </li>
                    <li class="p-2 bg-gray-50 rounded font-mono text-sm">
                        <span class="font-bold text-blue-600 mr-2">GET</span>{api_base_url}/health - Health check
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        // Cookie helpers
        const getCookie = (name) => {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            return parts.length === 2 ? parts.pop().split(';').shift() : null;
        }};

        const setCookie = (name, value) => {{
            const expires = new Date(Date.now() + 365 * 864e5).toUTCString();
            document.cookie = `${{name}}=${{value}}; expires=${{expires}}; path=/; SameSite=Lax`;
        }};

        const deleteCookie = (name) => {{
            document.cookie = `${{name}}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        }};

        // Login/Logout
        document.addEventListener('DOMContentLoaded', () => {{
            const email = getCookie('vanna_email');

            // Check if already logged in
            if (email) {{
                loginContainer.classList.add('hidden');
                loggedInStatus.classList.remove('hidden');
                chatSections.classList.remove('hidden');
                loggedInEmail.textContent = email;
            }}

            // Login button
            loginButton.addEventListener('click', () => {{
                const email = emailInput.value.trim();
                if (!email || !email.includes('@')) {{
                    alert('Please enter a valid email address');
                    return;
                }}
                setCookie('vanna_email', email);
                loginContainer.classList.add('hidden');
                loggedInStatus.classList.remove('hidden');
                chatSections.classList.remove('hidden');
                loggedInEmail.textContent = email;
            }});

            // Logout button
            logoutButton.addEventListener('click', () => {{
                deleteCookie('vanna_email');
                loginContainer.classList.remove('hidden');
                loggedInStatus.classList.add('hidden');
                chatSections.classList.add('hidden');
                emailInput.value = '';
            }});

            // Enter key
            emailInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') loginButton.click();
            }});
        }});
    </script>

    <script>
        // Artifact demo event listener
        document.addEventListener('DOMContentLoaded', () => {{
            const vannaChat = document.querySelector('vanna-chat');

            if (vannaChat) {{
                // Add artifact event listener to demonstrate external rendering
                vannaChat.addEventListener('artifact-opened', (event) => {{
                    const {{ artifactId, type, title, trigger }} = event.detail;

                    console.log('🎨 Artifact Event:', {{ artifactId, type, title, trigger }});

                    // For demo: open all artifacts externally
                    setTimeout(() => {{
                        const newWindow = window.open('', '_blank', 'width=900,height=700');
                        if (newWindow) {{
                            newWindow.document.write(event.detail.getStandaloneHTML());
                            newWindow.document.close();
                            newWindow.document.title = title || 'Vanna Artifact';
                            console.log(`📱 Opened ${{title}} in new window`);
                        }}
                    }}, 100);

                    // Prevent default in-chat rendering
                    event.detail.preventDefault();
                    console.log('✋ Showing placeholder in chat instead of full artifact');
                }});

                console.log('🎯 Artifact demo mode: All artifacts will open externally');
            }}
        }});

        // Fallback if web component doesn't load
        if (!customElements.get('vanna-chat')) {{
            setTimeout(() => {{
                if (!customElements.get('vanna-chat')) {{
                    document.querySelector('vanna-chat').innerHTML = `
                        <div class="p-10 text-center text-gray-600">
                            <h3 class="text-xl font-semibold mb-2">Vanna Chat Component</h3>
                            <p class="mb-2">Web component failed to load. Please check your connection.</p>
                            <p class="text-sm text-gray-400">
                                {('Loading from: local static assets' if dev_mode else f'Loading from: {cdn_url}')}
                            </p>
                        </div>
                    `;
                }}
            }}, 2000);
        }}
    </script>
</body>
</html>"""


# Backward compatibility - default production HTML
INDEX_HTML = get_index_html()
