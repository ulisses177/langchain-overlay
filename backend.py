import os
import shutil
import base64
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

class ChatBotBackend:
    def __init__(self, log_file="chat_log.md"):
        self.llm = Ollama(model="DolphinMem")
        self.llava = Ollama(model="llava")  # Load the llava model
        self.log_file = log_file
        self.memory = ConversationBufferMemory(return_messages=True)
        self.saved_images_dir = os.path.join(os.path.dirname(__file__), 'saved_images')
        os.makedirs(self.saved_images_dir, exist_ok=True)
        self.load_chat_history()

    def load_chat_history(self, file_path=None):
        if file_path:
            self.log_file = file_path
        self.memory.chat_memory.clear()  # Clear existing memory before loading
        try:
            with open(self.log_file, 'r') as file:
                for line in file:
                    if line.startswith("You:"):
                        self.memory.chat_memory.add_user_message(line[4:].strip())
                    elif line.startswith("Assistant:"):
                        self.memory.chat_memory.add_ai_message(line[10:].strip())
                    elif line.startswith("![Image]"):
                        # Add image as a plain message for now
                        self.memory.chat_memory.add_ai_message(line.strip())
        except FileNotFoundError:
            pass

    def append_to_log(self, role, message):
        with open(self.log_file, 'a') as file:
            if role == "Image":
                file.write(f"![Image]({message})\n")
            else:
                file.write(f"{role}: {message}\n")

    def get_full_chat_history(self):
        messages = self.memory.load_memory_variables({})['history']
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append(f"You: {msg.content}")
            elif isinstance(msg, AIMessage):
                if msg.content.startswith("![Image]"):
                    formatted_messages.append(msg.content)
                else:
                    formatted_messages.append(f"Assistant: {msg.content}")
        return "\n".join(formatted_messages)

    def generate_response(self, user_input):
        self.append_to_log("You", user_input)
        self.memory.chat_memory.add_user_message(user_input)

        recent_messages = self.memory.load_memory_variables({})['history'][-10:]
        context = "\n".join([msg.content for msg in recent_messages])

        response = self.llm.invoke(context)

        self.memory.chat_memory.add_ai_message(response)
        self.append_to_log("Assistant", response)
        return response

    def save_image(self, image_path):
        if not os.path.exists(image_path):
            return None, None
        image_name = os.path.basename(image_path)
        saved_image_path = os.path.join(self.saved_images_dir, image_name)
        os.makedirs(self.saved_images_dir, exist_ok=True)  # Ensure the directory exists
        shutil.copy(image_path, saved_image_path)
        self.append_to_log("Image", saved_image_path)
        
        # Generate a description for the image
        with open(saved_image_path, "rb") as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
        llm_with_image_context = self.llava.bind(images=[image_b64])
        image_description = llm_with_image_context.invoke("Describe this image with as few words as possible:")
        
        # Append the image description to the log and return it
        self.append_to_log("Assistant", image_description)
        return saved_image_path, image_description

    def save_chat_history(self, file_path):
        with open(file_path, 'w') as file:
            file.write(self.get_full_chat_history())
