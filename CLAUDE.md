# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal study project for learning LangGraph — a low-level stateful AI agent orchestration framework built on top of LangChain. The study plan (`StudyPlan.md`) covers 16 phases from basic graph concepts through production deployment. Content and comments are in Traditional Chinese (繁體中文).

## Development Environment

- **Python**: 3.13 (managed via `.python-version`)
- **Package manager**: uv
- **Primary dependency**: `langgraph>=1.1.6`

## Common Commands

```bash
# Install dependencies
uv sync

# Run main entry point
uv run python main.py

# Add a new dependency
uv add <package>
```

## Architecture

This is an early-stage learning repo with a single `main.py` entry point. As the study plan progresses, expect code organized around LangGraph concepts: `StateGraph` definitions, node functions, conditional edges, checkpointers, and multi-agent patterns.

## Key LangGraph Concepts (for context)

Core primitives used throughout: `StateGraph`, `Node`, `Edge`, `State` (via `TypedDict` or Pydantic), `Channel`, `Reducer`, `END`, `Command`. The study plan references `MessagesState` as the built-in message-based state schema and covers patterns like ReAct loops, supervisor/swarm multi-agent, subgraphs, and the functional API (`@entrypoint`, `@task`).

## Reference

- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Academy](https://academy.langchain.com/)
