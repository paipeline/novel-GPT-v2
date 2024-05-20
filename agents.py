import os
from langchain_openai import ChatOpenAI
from crewai import Agent
from tasks import Tasks
import time
from textwrap import dedent

class Agents:
    def __init__(self, llm, llm4o):
        self.llm = llm
        self.llm4o = llm4o
        self.agents = self.create_agents()

    def create_agents(self):
        
        title_generator = Agent(
            role='书名生成器',
            goal=dedent("""1.根据小说的大纲生成一个吸引人的书名。\
                2.与大纲设计师和章节作者合作，确保书名与故事的主题和角色一致。3.书名应简洁明了，不超过六个字。"""),
            verbose=True,
            memory=False,
            backstory='一个有创造力的专家，擅长想出吸引人和贴切的书名。',
            tools=[],
            llm=self.llm,
            allow_delegation=False,
            language="Chinese"
        )

        chapter_writer = Agent(
            role='章节作者',
            goal=dedent(''' 1. 人物角色用中文的。\
                2. 根据已开发的大纲和角色设计编写详细且引人入胜的小说内容。 \
                3. 确保不重复内容。语言应简洁明了。 \
                4. 应有适量的对话。 \
                5. 每章应足够长，至少3000个中文字符或3000个英文单词，以覆盖每章的主要目标。\
                6. 故事进展要快。\
                7. 段落之间不能一只在重复相同的内容。'''),
            verbose=True,
            memory=False,
            backstory=dedent("""一个以详细的叙事和复杂的角色和场景开发而闻名的熟练小说家。"""),
            tools=[],
            llm=self.llm4o,
            allow_delegation=False
        )

        outline_designer = Agent(
            role='大纲设计师',
            goal=dedent("""1. 为每一章制定一个全面的大纲，每章必须有一个对整体情节有贡献的目标和高潮点。 \
                2. 确定故事发生的主要设置，包括地点、时间和世界构建。 \
                3. 按照结构发展故事：开头、中间、高潮和结尾。 \
                4. 确保故事的整体基调与小说的前几章保持一致。 \
                5. 确定关键事件、冲突和解决方案。\
                6. 确保每个章节的开头都引人入胜并且都有结合前面章节的结尾铺垫，以保持故事的连贯性。"""),
            verbose=True,
            memory=False,
            backstory='在构建叙述结构和创建引人入胜的故事情节方面经验丰富。',
            tools=[],
            context="基于角色设计师和场景设计师开发的角色和场景设置。",
            llm=self.llm4o,
            allow_delegation=False
        )

        supervising_editor = Agent(
            role='监督编辑',
            goal=dedent("""1. 监督小说的发展，以确保从大纲到最终手稿的质量和连贯性。 \
                2. 检查整体风格及其与叙述基调的一致性。 \
                3. 确保所有主要角色在小说中得到充分发展，并确保这些变化是可信且引人入胜的。 \
                4. 保持小说的节奏，确保故事顺利发展，不会仓促或拖沓。 \
                5. 每章应足够长，至少2000个中文字符或2000个英文单词，以覆盖每章的主要目标。"""),
            verbose=True,
            memory=False,
            backstory='在管理大型写作项目方面经验丰富。',
            tools=[],
            allow_delegation=True,
            llm=self.llm4o,
        )

        scene_designer = Agent(
            role='场景设计师',
            goal=dedent("""1. 开发详细且引人入胜的场景描述，为小说的动作设置舞台。 \
                2. 在整个小说中保持一致性，以避免读者混淆，确保任何设置的变化都是合乎逻辑的。 \
                3. 确保所有阶段的方面都具有历史准确性，例如建筑、服装、社会规范。\
                4. 如有必要，使用设置象征诸如权力、死亡或自由等主题。"""),
            verbose=True,
            memory=False,
            backstory='擅长创造生动、沉浸式的设置，以增强叙事并支持角色行动。',
            tools=[],
            llm=self.llm4o,
            allow_delegation=False
        )

        character_designer = Agent(
            role='角色设计师',
            goal='1. 在每章编写之前开发深入的角色资料，以增强叙事。 \
                2. 确保每个人物的名字是中国大陆的名字。\
                2. 确保角色的资料（性格、动机、背景故事）支持他们在故事中的决定和行动。 \
                3. 在整个小说中保持角色的一致性，确保他们的发展与他们的行动一致。 \
                4. 描述角色之间的互动和关系，关系应动态并反映个人成长。 \
                5. 为每个角色设计独特的声音，反映他们的背景和个性。',
            verbose=True,
            memory=False,
            backstory='创造引人入胜且真实可信的角色。',
            tools=[],
            llm=self.llm4o,
            allow_delegation=False
        )

        markdown_formatter = Agent(
            role='Markdown格式化师',
            goal='1. 以markdown格式整理写好的内容以便数字出版。 \
                2. 将内容组织成逻辑结构，并应用每章的加粗标题。',
            verbose=True,
            memory=False,
            backstory='一个细致的格式化师，提升书籍的可读性和层次化呈现。',
            tools=[],
            llm=self.llm4o,
            allow_delegation=False
        )

        language_checker = Agent(
            role='语言检查员',
            goal='1. 确保内容以用户提供的指定语言撰写。 \
                2. 检查语法错误、标点和语法结构。 \
                3. 确保故事的语气适当。 \
                4. 提升句子的清晰度。 \
                5. 确保语言，包括词汇、成语和表达方式，反映故事发生的时间。\
                6. 确保使用简体中文名字',
            verbose=True,
            memory=False,
            backstory='多语言专家，确保语言的准确性和一致性。',
            tools=[],
            llm=self.llm4o,
            allow_delegation=False
        )

        return [supervising_editor, character_designer, scene_designer, outline_designer, title_generator, chapter_writer, markdown_formatter, language_checker]



