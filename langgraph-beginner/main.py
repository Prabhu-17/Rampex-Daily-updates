from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Define State
class StudentState(TypedDict):
    name: str
    marks: int
    result: str

# 2. Create Nodes
def check_marks(state: StudentState):
    if state["marks"] >= 50:
        return {"result": "Pass"}

    return {"result": "Fail"}

def generate_report(state: StudentState):
    print("Student:", state["name"])
    print("Marks:", state["marks"])
    print("Result:", state["result"])

    return {}

# 3. Create Graph
builder = StateGraph(StudentState)

# 4. Add Nodes
builder.add_node("check_marks", check_marks)
builder.add_node("generate_report", generate_report)

# 5. Add Edges
builder.add_edge(START, "check_marks")
builder.add_edge("check_marks", "generate_report")
builder.add_edge("generate_report", END)

# 6. Compile Graph
graph = builder.compile()

# 7. Execute
result = graph.invoke({
    "name": "Arun",
    "marks": 85,
    "result": ""
})

print(result)