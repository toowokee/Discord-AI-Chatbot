# Roadmap Updated 11/9/26

Feature requests, planned improvements, and long-term development goals for the chatbot project.

> This roadmap is subject to change as development progresses. Features may be added, modified, or removed based on project priorities.

## 🚧 Technical Improvements

- [ ] **Better Ollama Error Handling**
  - Provide clear, user-friendly error messages when Ollama isn't running.
  - Prevent silent failures and exposed stack traces.

- [ ] **Automatic Reconnection**
  - Implement automatic retries with exponential backoff.
  - Set a maximum retry limit to prevent endless connection attempts.

- [ ] **Model Availability Checks**
  - Verify that the configured model is installed at startup.
  - Display helpful errors when a model is unavailable.

- [ ] **Asynchronous Database Operations**
  - Prevent database operations from blocking the bot's event loop.

- [ ] **Structured Logging**
  - Implement structured JSON or key-value logging.
  - Include log levels, timestamps, and request/user identifiers.

- [ ] **Automated Testing**
  - Add unit tests for core functionality.
  - Add integration tests for AI providers and database operations.
  - Implement mocked LLM responses for predictable testing.

- [ ] **Docker Health Checks**
  - Add health checks for the chatbot, database, and AI provider.
  - Report unhealthy status when required services are unavailable.

- [ ] **Configuration Validation**
  - Validate environment variables and configuration files at startup.
  - Fail fast with clear, actionable error messages.

## ✨ New Features

- [ ] **Image Detection and Generation**
  - Detect and describe images sent by users using vision models.
  - Generate images from user-provided prompts.

- [ ] **Web Access**
  - Allow the chatbot to search the web for current information.
  - Support fetching and summarizing web pages.
  - Implement safeguards such as rate limits and domain restrictions.

- [ ] **Selectable Personalities**
  - Add selectable response styles and tones.
  - Examples: Friendly, Formal, Sarcastic, Professional, and Casual.

- [ ] **Multiple Languages and Custom Personas**
  - Automatically detect and respond in the user's language.
  - Support custom characters with individual names, backstories, and speaking styles.
  - Allow persona selection per user or server.

## 🧠 Smarter Context Handling

- [ ] **Message Reply Awareness**
  - Use replied-to messages as additional context when generating responses.

- [ ] **Multi-User Conversation Awareness**
  - Track who said what in group conversations.
  - Understand and reference users by name when appropriate.

- [ ] **Bot Interaction Detection**
  - Recognize when users are directly addressing the chatbot.
  - Detect mentions, replies to the bot, and direct questions.

- [ ] **Smarter Response Triggers**
  - Avoid responding to every message.
  - Respond when directly addressed or when a reply would be useful.
  - Support configurable cooldowns and trigger rules.

## 💾 Better Conversation Memory

- [ ] **Persistent Conversation History**
  - Store conversation history across restarts.

- [ ] **Long-Term Memory**
  - Store important facts separately from regular chat history.
  - Remember preferences, names, and other relevant details.

- [ ] **Conversation Summarization**
  - Summarize older conversations to conserve context window space.
  - Preserve important information when older messages are condensed.

- [ ] **User and Server Memory Isolation**
  - Keep memories separated between users and servers.
  - Protect user privacy through proper data isolation.
  - Add commands to view, edit, and delete stored memories.

## 🤖 Multiple AI Providers

- [ ] **Ollama Support**
  - Support locally hosted AI models through Ollama.

- [ ] **Groq Support**
  - Support hosted inference through Groq.

- [ ] **OpenAI-Compatible API Support**
  - Support any service that follows the OpenAI API format.

- [ ] **Provider Switching**
  - Allow users to configure their preferred AI provider.
  - Implement a common provider interface to simplify adding new providers.

- [ ] **Automatic Provider Fallback**
  - Optionally switch to a backup provider when the primary provider becomes unavailable.

---

## 💡 Suggestions

Have an idea, feature request, or improvement?

Feel free to open an issue or submit a pull request with your suggestions.
