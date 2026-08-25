# Landslide Image Verification & Alert Agent

This microservice provides an agentic pipeline for analyzing uploaded landslide images using Groq's Vision API and LangGraph. It exposes a FastAPI REST API and includes a drop-in React component for the frontend.

## Architecture
- **Backend:** FastAPI, LangGraph, Groq, SQLite
- **Frontend:** React functional component
- **Storage:** Local SQLite database & file storage

## Setup Instructions

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Install dependencies (it is recommended to use a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `backend` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   AI_REJECTION_THRESHOLD=70
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 2. Frontend Setup

1. Copy the `frontend/LandslideReportUploader.jsx` component into your existing React project (e.g., inside TerraSense/Client/src/components).
2. The component is entirely self-contained and uses vanilla CSS (via inline styles) for a modern, glassmorphic look. 
3. Import and use it in your React app:
   ```jsx
   import LandslideReportUploader from './components/LandslideReportUploader';

   function App() {
     return (
       <div>
         <LandslideReportUploader apiBaseUrl="http://localhost:8000" />
       </div>
     );
   }
   ```

## Adjustable Prompts

The prompts used for the Groq Vision model are defined in `backend/pipeline.py`. They are extracted here so the team can review and tune the rubrics as needed.

### 1. Authenticity Prompt
*Used to check if an uploaded image is AI-generated.*

```text
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
```

### 2. Severity Analysis Prompt
*Used to classify the severity of the landslide if the image passes authenticity checks.*

```text
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
```
