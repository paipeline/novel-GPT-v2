from crewai import Task, Crew, Process
import os
from langchain_openai import ChatOpenAI
from crewai import Agent
import time
class Tasks:
    def __init__(self, agents):
        self.agents = agents
        self.crew = Crew(
            agents=self.agents,
            process=Process.sequential,
            memory=False,
            cache=True,
            max_rpm=100,  # if mixtal max_rpm=20
            llm=agents[0].llm,
            share_crew=True
        )
        self.prev_content = None
    def callback_func(self,output):
        # Print when task is finished
        message = f"""  \n 
        ----任务完成!----
        Task: {output.description}
        Output: {output.raw_output}
        ---------------- \n
        """
        print(message)
        
        # Save output to log.md
        with open("log.md", "a") as file:
            file.write(message)

            
    def prepare_for_chapters(self, inputs, story_file):
        outline_task = Task(
            
            description=f"每章的具体概要为了让之后生成文章做准备。主题：{inputs['topic']} 章节数量：{inputs['cnt_chapter']}",
            expected_output='小说每章的详细大纲。',
            agent=self.agents[0],
            output_file="temp/outline.md",
            callback = self.callback_func
        )
        # scene_task = Task(
        #     description=f"根据大纲制定主要情节点的场景设置。主题：{inputs['topic']}",
        #     expected_output='详细的场景设置，准备好进行叙述开发。',
        #     agent=self.agents[1],
        #     depends_on = outline_task,
        #     input = outline_task.output,
        #     output_file="temp/scenes.md",
        #     callback = self.callback_func

        # )
        # character_task = Task(
            
        #     description=f"根据小说的大纲开发详细的角色资料。主题：{inputs['topic']}",
        #     expected_output='准备纳入小说的深入角色资料。',
        #     agent=self.agents[2],
        #     output_file="temp/characters.md",
        #     callback = self.callback_func

        # )

        # self.crew.tasks = [scene_task, outline_task, character_task]
        
        self.crew.tasks = [outline_task]
        self.crew.kickoff(inputs=inputs)

        # make log of outputs
        outputs = {}
        for task in self.crew.tasks:
            with open(task.output_file, 'r') as file:
                outputs[task.description] = file.read()
        return outputs

    def generate_book_title(self, inputs,outline):
        title_task = Task(
            description="结合用户输入的主题和风格： {inputs['topic']} 小说的大纲:{outline} 生成一个吸引人的书名。",
            expected_output='现代文学书名，字数不超过六个字。',
            agent=self.agents[3],
            output_file="temp/title.txt",
            callback = self.callback_func,
        )
        self.crew.tasks = [title_task]
        self.crew.kickoff(inputs={})
        with open(title_task.output_file, 'r') as file:
            title = file.read().strip()
        return title

    def process_chapters(self, inputs, story_file, prev_content = None):
        cnt_chapter = 10
        for chapter_number in range(1, cnt_chapter + 1):
            with open("temp/outline.md", 'r') as file:
                outline = file.read().strip()
                
            chapter_outline_task = Task(
                
                description=f"""
                根据小说的大纲: {outline}，\
                使用语言:{inputs["language"]} \
                制定第{chapter_number}章的更详细的针对章节的大纲。\
                """,
                expected_output=f"第{chapter_number}章的详细大纲。",
                agent=self.agents[4],
                context=None,
                input = outline, # fixed：outline作为输入，让outline_designer更加准确的根据outline生成chapter outline
                output_file=f"temp/chapter_{chapter_number}_outline.md"
            )
            self.crew.tasks = [chapter_outline_task]
            self.crew.kickoff(inputs=inputs)

            with open(chapter_outline_task.output_file, 'r') as file:
                chapter_outline = file.read().strip()

            write_task = Task(
                description=f"""根据第{chapter_number}章的大纲编写内容。\n
                章节要至少4千个中文字\
                如果不是第一章请用上个章节的输出做为背景：{prev_content} 去续写目前章节。""",
                expected_output=f"只输出起草的第{chapter_number}章，准备审核。",
                agent=self.agents[5],
                context= [chapter_outline_task],
                callback = self.callback_func
            )

            review_task = Task(
                description=f"""
                审核第{chapter_number}章的一致性，\
                前一章节的关联性和叙述流畅性。\
                前一章的内容 {prev_content}""",
                expected_output=f"只提供编辑完善的第{chapter_number}标题和章节。不要说任何其他事情",
                agent=self.agents[0],
                context=[write_task],
                callback = self.callback_func

            )

            language_check_task = Task(
                description=f"确保第{chapter_number}章以{inputs['language']}撰写，并审核其一致性、语言和叙述流畅性。只提供章节标题和内容。不要summary",
                expected_output=f"第{chapter_number}章验证完的章节标题以及内容, 其他的一律不要输出尤其是system message。",
                agent=self.agents[6],
                depends_on=review_task,
                input=review_task.output,  #fixed： review_task 的输出作为输入
                output_file=f"temp/checked_chapter_{chapter_number}.md",
                callback = self.callback_func

            )

            self.crew.tasks = [write_task, review_task, language_check_task]
            self.crew.kickoff(inputs=inputs)

            # Append chapter tasks outputs to story.md
            with open(language_check_task.output_file, 'r') as file:
                content = file.read().replace("Chapter verified for Chinese language accuracy.", "")
                if chapter_number > 1:
                    content = f"### 第{chapter_number}章\n\n" + content
                self.append_to_story(story_file, content)

            time.sleep(1)  # To handle rate limits
            prev_content = content

        markdown_format_task = Task(
            description='以markdown格式整理书籍内容。',
            agent=self.agents[7],
            expected_output='以markdown格式整理的整本书内容。',
            output_file=story_file,
            callback = self.callback_func

        )

        self.crew.tasks = [markdown_format_task]
        self.crew.kickoff(inputs=inputs)
        
        

    def append_to_story(self, story_file, content):
        with open(story_file, "a") as file:
            file.write(content + "\n\n")


