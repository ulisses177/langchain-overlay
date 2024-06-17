from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

class ChatBotBackend:
    def __init__(self, log_file="chat_log.txt"):
        self.llm = Ollama(model="DolphinMem")
        self.log_file = log_file
        self.memory = ConversationBufferMemory(return_messages=True)
        self.load_chat_history()

    def load_chat_history(self):
        try:
            with open(self.log_file, 'r') as file:
                for line in file:
                    if line.startswith("You:"):
                        self.memory.chat_memory.add_user_message(line[4:].strip())
                    elif line.startswith("Assistant:"):
                        self.memory.chat_memory.add_ai_message(line[10:].strip())
        except FileNotFoundError:
            pass

    def append_to_log(self, role, message):
        with open(self.log_file, 'a') as file:
            file.write(f"{role}: {message}\n")

    def get_full_chat_history(self):
        messages = self.memory.load_memory_variables({})['history']
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append(f"You: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted_messages.append(f"Assistant: {msg.content}")
        return "\n".join(formatted_messages)

    def generate_response(self, user_input):
        self.append_to_log("You", user_input)
        self.memory.chat_memory.add_user_message(user_input)

        # Retrieve the last 10 messages
        recent_messages = self.memory.load_memory_variables({})['history'][-10:]
        context = "\n".join([msg.content for msg in recent_messages])
        
        response = self.llm.invoke(context)
        
        self.memory.chat_memory.add_ai_message(response)
        self.append_to_log("Assistant", response)
        return response
