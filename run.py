import os
from langchain_openai import ChatOpenAI
from crewai import Agent
import time
from agents import Agents
from tasks import Tasks
class Run:
    def __init__(self):
        # Set environment variables for API keys

        os.environ["SERPER_API_KEY"] = ""
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["GROQ_API_KEY"] = ""
        # Initialize LLM clients
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")
        self.llm4o = ChatOpenAI(model="gpt-4o")
        self.llmgroq = ChatOpenAI(
            openai_api_base="https://api.groq.com/openai/v1",
            openai_api_key=os.getenv("GROQ_API_KEY"),
            model_name="mixtral-8x7b-32768"
        )
        self.agents = Agents(self.llm, self.llm4o).agents
        self.tasks = Tasks(self.agents)
        
        


    def execute(self, user_input):
        
        outputs = self.tasks.prepare_for_chapters(inputs=user_input, story_file="temp/temp_story.md")
        outline = outputs[f"每章的具体概要为了让之后生成文章做准备。主题：{user_input['topic']} 章节数量：{user_input['cnt_chapter']}"]
        book_title = self.tasks.generate_book_title(user_input,outline)
        story_file_name = book_title.replace(" ", "_") + ".md"
        story_file = os.path.join(os.path.join(os.getcwd(),"novels"), story_file_name)

        #Write book title to story file
        with open(story_file, "w") as file:
            file.write(f"# {book_title}\n\n")

        
        for description, content in outputs.items():
            self.tasks.append_to_story(story_file, content)

        self.tasks.process_chapters(inputs=user_input, story_file=story_file)
