from fastapi import APIRouter, HTTPException
from models.schemas import AgentRequest, AgentResponse
from agents.ocr_agent import OCRAgent
from agents.vector_agent import VectorAgent
from agents.extraction_agent import ExtractionAgent
from agents.summary_agent import SummaryAgent

router = APIRouter()

# Initialize agents
agents = {
    "ocr": OCRAgent(),
    "vector": VectorAgent(),
    "extraction": ExtractionAgent(),
    "summary": SummaryAgent()
}

@router.post("/agents/{agent_type}/execute", response_model=AgentResponse)
async def execute_agent(agent_type: str, request: AgentRequest):
    """Execute a specific agent with provided input"""
    if agent_type not in agents:
        raise HTTPException(
            status_code=404,
            detail=f"Agent type '{agent_type}' not found. Available agents: {list(agents.keys())}"
        )

    agent = agents[agent_type]

    try:
        result = await agent.process(
            input_data=request.input,
            parameters=request.parameters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "type": agent_type,
                "name": agent.name,
                "layer": agent.layer
            }
            for agent_type, agent in agents.items()
        ]
    }

@router.get("/agents/{agent_type}")
async def get_agent_info(agent_type: str):
    """Get information about a specific agent"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")

    agent = agents[agent_type]
    return {
        "type": agent_type,
        "name": agent.name,
        "layer": agent.layer,
        "description": agent.__doc__ or "No description available"
    }
