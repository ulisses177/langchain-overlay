# LangChain Overlay

LangChain Overlay is an interactive chatbot application that utilizes LangChain's memory capabilities and Ollama LLM to provide a persistent and context-aware conversational experience. The overlay provides a user-friendly interface that stays on top of other windows, making it easy to interact with the chatbot while using other applications.

## Features

- **Persistent Chat Memory:** Utilizes LangChain's `ConversationBufferMemory` to maintain a consistent conversation history across sessions.
- **Context-Aware Responses:** The chatbot uses the last 10 messages to generate contextually relevant responses.
- **Overlay Interface:** A frameless, translucent window that stays on top of other windows, providing easy access to the chatbot.
- **Speech Recognition:** Allows users to input messages via speech using the `speech_recognition` library.
- **System Tray Integration:** Includes a system tray icon for easy access and control of the overlay.

## Installation

### Prerequisites

- Python 3.7 or higher
- Pip package manager

### Libraries

Install the required libraries using pip:

```bash
pip install langchain_community PyQt5 speech_recognition
