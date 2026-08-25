import os
import json
import base64
from typing import Dict, Any, TypedDict
from pydantic import ValidationError
from groq import Groq
from langgraph.graph import StateGraph, END
from schemas import AuthenticityCheckResult, SeverityAnalysisResult

# Prompts
AUTHENTICITY_PROMPT = """
Analyze this image for signs of AI generation. Look for forensic indicators such as:
- Unnatural lighting or impossible shadows
- Texture anomalies or over-smoothed surfaces
- Implausible geometry or perspective errors
- Inconsistent noise patterns
- Absence of normal camera lens artifacts

Respond ONLY with valid JSON in this exact structure:
{
  "is_ai_generated": true/false,
  "confidence": 0-100,
  "reasoning": "detailed explanation"
}
"""

SEVERITY_PROMPT = """
Assess the landslide severity in this image. Look for:
- Soil or debris displacement
- Structural damage to buildings or infrastructure
- Debris spread and type (rocks, mud, trees)
- Blockage of roads or waterways
- Active-movement risk indicators

Respond ONLY with valid JSON in this exact structure:
{
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "confidence": 0-100,
  "affected_indicators": ["indicator1", "indicator2"],
  "reasoning": "detailed explanation",
  "recommended_action": "recommended immediate action"
}
"""

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        # Determine mime type
        ext = image_path.lower().split('.')[-1]
        mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
        return f"data:image/{mime};base64,{encoded}"

def _run_groq_vision_with_retry(client: Groq, image_data_uri: str, prompt: str, schema_cls, retries=1):
    for attempt in range(retries + 1):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_uri,
                                },
                            },
                        ],
                    }
                ],
                model="llama-3.2-90b-vision-preview",
                response_format={"type": "json_object"}
            )
            
            content = chat_completion.choices[0].message.content
            parsed_json = json.loads(content)
            return schema_cls(**parsed_json)
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == retries:
                raise Exception(f"Failed to parse Groq response after {retries} retries: {str(e)}")
            continue

class AgentState(TypedDict):
    report_id: str
    image_path: str
    db_session: Any
    
    # Results
    authenticity_result: AuthenticityCheckResult
    severity_result: SeverityAnalysisResult
    status: str

def authenticity_node(state: AgentState) -> Dict:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    image_uri = encode_image(state["image_path"])
    
    try:
        result = _run_groq_vision_with_retry(
            client=client,
            image_data_uri=image_uri,
            prompt=AUTHENTICITY_PROMPT,
            schema_cls=AuthenticityCheckResult
        )
        
        # Check EXIF (simplified check)
        from PIL import Image
        try:
            with Image.open(state["image_path"]) as img:
                exif = img.getexif()
                if not exif and result.is_ai_generated:
                    # Lack of EXIF reinforces AI generation if vision model also thinks so
                    result.confidence = min(100.0, result.confidence + 10.0)
        except Exception:
            pass
            
        threshold = float(os.environ.get("AI_REJECTION_THRESHOLD", "70"))
        if result.is_ai_generated and result.confidence > threshold:
            status = "rejected"
        else:
            status = "processing"
            
        return {"authenticity_result": result, "status": status}
        
    except Exception as e:
        print(f"Authenticity check failed: {e}")
        return {"status": "error"}

def severity_node(state: AgentState) -> Dict:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    image_uri = encode_image(state["image_path"])
    
    try:
        result = _run_groq_vision_with_retry(
            client=client,
            image_data_uri=image_uri,
            prompt=SEVERITY_PROMPT,
            schema_cls=SeverityAnalysisResult
        )
        return {"severity_result": result, "status": "posted"}
    except Exception as e:
        print(f"Severity check failed: {e}")
        return {"status": "error"}

def route_next(state: AgentState) -> str:
    if state.get("status") == "rejected":
        return END
    if state.get("status") == "error":
        return END
    return "severity"

# Build Graph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("authenticity", authenticity_node)
graph_builder.add_node("severity", severity_node)
graph_builder.set_entry_point("authenticity")
graph_builder.add_conditional_edges(
    "authenticity",
    route_next,
    {
        END: END,
        "severity": "severity"
    }
)
graph_builder.add_edge("severity", END)
pipeline_app = graph_builder.compile()

def process_image_pipeline(report_id: str, image_path: str, session: Any):
    # Initialize state
    initial_state = {
        "report_id": report_id,
        "image_path": image_path,
        "db_session": session,
    }
    
    # Run pipeline
    final_state = pipeline_app.invoke(initial_state)
    return final_state
