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
            memory=True,
            cache=True,
            max_rpm=100,  # if mixtal max_rpm=20
            llm=agents[0].llm,
            share_crew=True
        )

    def prepare_for_chapters(self, inputs, story_file):
        outline_task = Task(
            description=f"制定包含主要情节点和角色弧的大纲。主题：{inputs['topic']}",
            expected_output='小说的详细大纲。',
            agent=self.agents[0],
            output_file="temp/outline.md"
        )
        scene_task = Task(
            description=f"根据大纲制定主要情节点的场景设置。主题：{inputs['topic']}",
            expected_output='详细的场景设置，准备好进行叙述开发。',
            agent=self.agents[1],
            output_file="temp/scenes.md"
        )
        character_task = Task(
            description=f"根据小说的大纲开发详细的角色资料。主题：{inputs['topic']}",
            expected_output='准备纳入小说的深入角色资料。',
            agent=self.agents[2],
            output_file="temp/characters.md"
        )

        self.crew.tasks = [scene_task, outline_task, character_task]
        self.crew.kickoff(inputs=inputs)

        # Retrieve and store task outputs
        outputs = {}
        for task in self.crew.tasks:
            with open(task.output_file, 'r') as file:
                outputs[task.description] = file.read()

        return outputs

    def generate_book_title(self, outline):
        title_task = Task(
            description="根据小说的大纲生成一个吸引人的书名。",
            expected_output='现代文学书名，字数不超过六个字。',
            agent=self.agents[3],
            input=outline,
            output_file="title.txt"
        )
        self.crew.tasks = [title_task]
        self.crew.kickoff(inputs={})
        with open(title_task.output_file, 'r') as file:
            title = file.read().strip()
        return title

    def process_chapters(self, inputs, story_file):
        cnt_chapter = 10
        for chapter_number in range(1, cnt_chapter + 1):
            chapter_outline_task = Task(
                description=f"""根据小说的大纲，制定第{chapter_number}章的详细大纲。""",
                expected_output=f"第{chapter_number}章的详细大纲。",
                agent=self.agents[4],
                context=None,
                output_file=f"temp/chapter_{chapter_number}_outline.md"
            )
            self.crew.tasks = [chapter_outline_task]
            self.crew.kickoff(inputs=inputs)

            with open(chapter_outline_task.output_file, 'r') as file:
                chapter_outline = file.read().strip()

            write_task = Task(
                description=f"根据第{chapter_number}章的详细大纲编写内容。",
                expected_output=f"起草的第{chapter_number}章，准备审核。",
                agent=self.agents[5],
                input=chapter_outline,
            )

            review_task = Task(
                description=f"审核第{chapter_number}章的一致性、语言和叙述流畅性。只提供章节标题和内容。",
                expected_output=f"编辑完善的第{chapter_number}章。",
                agent=self.agents[0]
            )

            language_check_task = Task(
                description=f"确保第{chapter_number}章以{inputs['language']}撰写，并审核其一致性、语言和叙述流畅性。只提供章节标题和内容。",
                expected_output=f"验证为{inputs['language']}语言准确性的第{chapter_number}章。",
                agent=self.agents[6],
                output_file=f"temp/checked_chapter_{chapter_number}.md"
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

        markdown_format_task = Task(
            description='以markdown格式整理书籍内容。',
            agent=self.agents[7],
            expected_output='以markdown格式整理的整本书内容。',
            output_file=story_file
        )

        self.crew.tasks = [markdown_format_task]
        self.crew.kickoff(inputs=inputs)

    def append_to_story(self, story_file, content):
        with open(story_file, "a") as file:
            file.write(content + "\n\n")


