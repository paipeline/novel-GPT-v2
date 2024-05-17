# CrewAI Novel Generator

这是一个基于 CrewAI 框架的自动小说生成项目。该项目通过定义多个角色代理和任务，协同生成一部现代都市搞笑小说。

## 目录

1. [简介](#简介)
2. [环境设置](#环境设置)
3. [使用说明](#使用说明)
4. [代码结构](#代码结构)
5. [代理定义](#代理定义)
6. [任务定义](#任务定义)
7. [执行流程](#执行流程)
8. [结论](#结论)

## 简介

该项目利用 CrewAI 框架生成小说，通过多个代理角色的协同工作，创建结构化和连贯的小说内容。每个代理都有明确的角色和目标，确保小说的各个方面都能高效处理。

## 环境设置

在运行代码之前，需要设置以下环境变量来提供必要的 API 密钥：

```bash
export SERPER_API_KEY="your_serper_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export GROQ_API_KEY="your_groq_api_key"

