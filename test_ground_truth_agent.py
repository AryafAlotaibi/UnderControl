from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from rag.retriever import (
    GroundTruthRetriever,
    build_ground_truth_rag_tool,
)
from llm.model import create_agent_llm


TEST_PROMPT = PromptTemplate.from_template(
    """
You are testing the Ground Truth RAG integration.

Available tools:
{tools}

Tool names:
{tool_names}

Your task is to retrieve historical project evidence using
search_ground_truth.

Ground Truth contains historical reference data only.
Do not treat retrieved information as facts about a current project.

You MUST follow this ReAct format:

Question: {input}

Thought: determine what historical evidence should be retrieved.

Action: choose a tool from [{tool_names}]

Action Input: provide the search query.

Stop immediately after Action Input and wait for the executor
to provide the Observation.

After receiving the Observation:

Thought: I now have enough historical evidence.

Final Answer: briefly summarize the retrieved historical evidence.

Do not create your own Observation.
Do not say that a tool is unavailable unless the executor returns an error.

{agent_scratchpad}
"""
)


def main():
    print("Building Ground Truth tool...")

    retriever = GroundTruthRetriever()
    ground_truth_tool = build_ground_truth_rag_tool(retriever)

    tools = [ground_truth_tool]

    llm = create_agent_llm()

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=TEST_PROMPT,
        stop_sequence=False,
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
    )

    result = executor.invoke(
        {
            "input": (
                "Find historical project cases involving blocked tasks, "
                "external vendor dependencies, and delivery delay risk."
            )
        }
    )

    print("\nFinal result:")
    print(result["output"])


if __name__ == "__main__":
    main()