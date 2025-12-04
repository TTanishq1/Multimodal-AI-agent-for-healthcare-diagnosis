# Complete Workflow Documentation - Multimodal AI Medical Agent
## Hinglish में Complete System Explanation

### Table of Contents (विषय सूची)
1. [System Overview](#system-overview)
2. [Phase 1: Setup & Initialization](#phase-1-setup--initialization)
3. [Phase 2: User Input Processing](#phase-2-user-input-processing)
4. [Phase 3: Multimodal Analysis](#phase-3-multimodal-analysis)
5. [Phase 4: Medical Assessment](#phase-4-medical-assessment)
6. [Phase 5: Result Generation](#phase-5-result-generation)
7. [Phase 6: Chat Functionality](#phase-6-chat-functionality)
8. [Complete Code Flow](#complete-code-flow)

---

## System Overview (सिस्टम का सारांश)

Yeh ek **Multimodal AI Medical Agent** hai jo:
- **Audio Input** - Patient ki voice ko text mein convert karta hai
- **Image Input** - Medical images ko analyze karta hai
- **LLM Processing** - Groq API se medical diagnosis generate karta hai
- **Text-to-Speech** - Doctor ka response audio mein convert karta hai
- **Chat Interface** - Real-time conversation support karta hai

### Architecture (आर्किटेक्चर)

```
User Input (Audio/Image)
    ↓
Gradio UI (gradio_app.py)
    ↓
API Local (app/api_local.py) - Parallel Processing
    ├─→ Audio Transcription (voice_of_the_patient.py)
    └─→ Image Analysis (brain_of_the_doctor.py)
    ↓
Multimodal Assessment (brain_of_the_doctor.py)
    ├─→ History Service (app/services/history_service.py)
    ├─→ Fusion Service (app/services/fusion_service.py)
    └─→ Confidence Service (app/services/confidence_service.py)
    ↓
Result Generation
    ├─→ Text Formatting
    └─→ Voice Generation (voice_of_the_doctor.py)
    ↓
UI Display + Chat Interface
```

---

## Phase 1: Setup & Initialization (सेटअप और शुरुआत)

### Step 1.1: Environment Setup

**File: `gradio_app.py` (Lines 1-4)**
```python
from dotenv import load_dotenv
load_dotenv()
```

**Explanation:**
- `.env` file se environment variables load hote hain
- `GROQ_API_KEY` aur `ELEVENLABS_API_KEY` access karne ke liye zaroori hai
- Application start hone se pehle yeh zaroori hai

**File: `brain_of_the_doctor.py` (Lines 1-3)**
```python
from dotenv import load_dotenv
load_dotenv()
```

**File: `voice_of_the_patient.py` (Lines 1-3)**
```python
from dotenv import load_dotenv
load_dotenv()
```

**Why Multiple Files?**
- Har module independently `.env` load karta hai
- Import order independent hai
- Error resilience improve hoti hai

### Step 1.2: LLM Client Initialization

**File: `gradio_app.py` (Lines 15-23)**
```python
def _get_llm_client():
    """Create LLM client if API key is available, otherwise return None."""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            return GroqLLMClient(api_key=api_key)
    except Exception as e:
        print(f"Could not create LLM client: {e}. Using fallback mode.")
    return None
```

**Explanation:**
- API key check karta hai
- Agar valid ho, toh `GroqLLMClient` banata hai
- Agar na ho, toh `None` return karta hai (fallback mode)
- **Fallback Mode:** LLM ke bina bhi app kaam karta hai (deterministic heuristics use hote hain)

**File: `brain_of_the_doctor.py` (Lines 32-58)**
```python
class GroqLLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be set")
        self.client = Groq(api_key=self.api_key)
        self.model = model
```

**Explanation:**
- Groq API client banata hai
- Default model: `llama-3.3-70b-versatile` (fast aur accurate)
- Model change kar sakte hain (speed vs accuracy trade-off)

### Step 1.3: UI Initialization

**File: `gradio_app.py` (Lines 196-244)**
```python
with gr.Blocks(title="AI Doctor with Vision and Voice") as iface:
    state = gr.State({})
    
    # Left Column: Input & Results
    with gr.Column(scale=1):
        audio_input = gr.Audio(...)
        image_input = gr.Image(...)
        submit_btn = gr.Button("🔍 Analyze", variant="primary")
        # Output fields...
    
    # Right Column: Chat
    with gr.Column(scale=1):
        chatbot = gr.Chatbot(...)
        chat_input = gr.Textbox(...)
        chat_btn = gr.Button("💬 Send Message", variant="primary")
```

**Explanation:**
- Gradio Blocks UI create karta hai
- Two columns: Input/Results (left) aur Chat (right)
- Session state maintain karta hai
- Event handlers attach karta hai

---

## Phase 2: User Input Processing (यूजर इनपुट प्रोसेसिंग)

### Step 2.1: User Submits Data

**File: `gradio_app.py` (Lines 43-52)**
```python
def submit_callback(audio_filepath, image_filepath, patient_id, session_state):
    llm_client = _get_llm_client()
    
    result = api_local.submit_record(
        audio_filepath=audio_filepath,
        image_filepath=image_filepath,
        patient_id=patient_id or None,
        llm_client=llm_client,
    )
```

**Explanation:**
- User "Analyze" button click karta hai
- Audio file path aur image file path receive hote hain
- LLM client banaya jata hai (agar available ho)
- `api_local.submit_record()` call hota hai (main processing)

### Step 2.2: Parallel Processing Setup

**File: `app/api_local.py` (Lines 122-162)**
```python
def submit_record(...):
    # Parallel processing: Transcribe audio and analyze image simultaneously
    def transcribe_audio():
        """Transcribe audio in parallel thread."""
        if not audio_filepath:
            return "No audio was provided.", 0.4
        try:
            api_key = os.environ.get("GROQ_API_KEY")
            transcript = transcribe_with_groq(
                GROQ_API_KEY=api_key,
                audio_filepath=audio_filepath,
                stt_model="whisper-large-v3-turbo",
            )
            return transcript, 0.75
        except Exception as e:
            return f"[Audio transcription unavailable: {str(e)}...]", 0.3
    
    def analyze_image():
        """Analyze image in parallel thread."""
        return _simple_image_summary(image_filepath)
    
    # Run both tasks in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        if audio_filepath:
            futures['audio'] = executor.submit(transcribe_audio)
        if image_filepath:
            futures['image'] = executor.submit(analyze_image)
        
        # Wait for results
        for key, future in futures.items():
            result = future.result()
            if key == 'audio':
                transcript, transcript_conf = result
            elif key == 'image':
                img = result
```

**Explanation:**
- **Parallel Processing:** Dono tasks simultaneously start hote hain
- **ThreadPoolExecutor:** 2 parallel threads
- **Benefits:** 40-50% faster execution
- **Error Handling:** Agar ek fail ho, toh dusra continue karta hai

### Step 2.3: Audio Transcription

**File: `voice_of_the_patient.py` (Lines 72-82)**
```python
def transcribe_with_groq(stt_model, audio_filepath, GROQ_API_KEY):
    client = Groq(api_key=GROQ_API_KEY)
    audio_file = open(audio_filepath, "rb")
    transcription = client.audio.transcriptions.create(
        model=stt_model,
        file=audio_file,
        language="en"
    )
    return transcription.text
```

**Explanation:**
- Groq Whisper API use karta hai
- Model: `whisper-large-v3-turbo` (fast aur accurate)
- Audio file ko API ko bhejta hai
- Transcribed text return karta hai

**Example:**
- Input: Audio file with "I have a wart on my foot"
- Output: "I have a wart on my foot"

### Step 2.4: Image Analysis

**File: `app/api_local.py` (Lines 18-101)**
```python
def _simple_image_summary(image_path: Optional[str]) -> Dict[str, Any]:
    if not image_path:
        return {"summary": "No image was provided.", "confidence": 0.4}
    
    try:
        from brain_of_the_doctor import encode_image, analyze_image_with_query
        
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            encoded_img = encode_image(image_path)
            query = """You are a medical imaging specialist..."""
            
            vision_result = analyze_image_with_query(
                query=query,
                model="llama-3.2-90b-vision-preview",
                encoded_image=encoded_img
            )
            return {"summary": vision_result, "confidence": 0.85}
    except Exception as e:
        print(f"Groq vision API failed: {e}. Using fallback...")
    
    # Fallback based on filename
    name = os.path.basename(image_path).lower()
    if "acne" in name or "pimple" in name:
        return {"summary": "Photo of facial skin with multiple small red spots...", "confidence": 0.75}
    return {"summary": "Photo of skin with a localised change...", "confidence": 0.6}
```

**Explanation:**
- Image ko base64 mein encode karta hai
- Groq Vision API ko detailed prompt ke saath bhejta hai
- Model: `llama-3.2-90b-vision-preview` (fast vision model)
- Agar API fail ho, toh filename se guess karta hai

**File: `brain_of_the_doctor.py` (Lines 124-169)**
```python
def encode_image(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image_with_query(query: str, model: str, encoded_image: str) -> str:
    client = Groq(api_key=api_key, timeout=30.0)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ],
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=messages, 
        model=model,
        max_tokens=1000,
        temperature=0.2
    )
    return chat_completion.choices[0].message.content
```

**Explanation:**
- Image ko base64 string mein convert karta hai
- Multimodal message banata hai (text + image)
- Vision API call karta hai
- Response text return karta hai

**Example:**
- Input: Image of wart on foot
- Output: "Image shows a plantar wart on the foot with characteristic black dots (thrombosed capillaries) and rough surface texture..."

---

## Phase 3: Multimodal Analysis (मल्टीमोडल विश्लेषण)

### Step 3.1: History Retrieval

**File: `app/services/history_service.py` (Lines 65-102)**
```python
def get_history_summary(patient_id: Optional[str]) -> str:
    conn = _get_conn()
    cur = conn.execute(
        """
        SELECT fusion_result_json, timestamp
        FROM visits
        WHERE patient_id = ?
        ORDER BY id DESC
        LIMIT 3
        """,
        (patient_id or "anonymous",),
    )
    rows = cur.fetchall()
    
    if not rows:
        return "No significant prior history is recorded for this patient."
    
    diagnoses = []
    for fusion_json, ts in rows:
        data = json.loads(fusion_json or "{}")
        diag = data.get("preliminary_diagnosis") or "unspecified issue"
        diagnoses.append(f"{diag} ({ts})")
    
    return f"Previous visits suggest: {'; '.join(diagnoses)}"
```

**Explanation:**
- SQLite database se last 3 visits fetch karta hai
- Diagnoses ko summary format mein combine karta hai
- Format: "Previous visits suggest: diagnosis1 (timestamp1); diagnosis2 (timestamp2); ..."

### Step 3.2: Multimodal Assessment

**File: `brain_of_the_doctor.py` (Lines 174-222)**
```python
def get_multimodal_assessment(
    image_summary: str,
    image_conf: float,
    transcript: str,
    transcript_conf: float,
    patient_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    # 1. Get history
    history_summary = get_history_summary(patient_id)
    
    # 2. Fuse all information
    fusion_result = fuse(
        image_summary=image_summary,
        image_conf=image_conf,
        transcript=transcript,
        transcript_conf=transcript_conf,
        history_summary=history_summary,
        llm_client=llm_client,
    )
    
    # 3. Compute confidence and triage
    action_result = compute_action(
        fusion_conf=fusion_result.get("fusion_confidence", 0.5),
        image_conf=image_conf,
        transcript_conf=transcript_conf,
        fused_findings=fusion_result.get("simple_findings"),
        conflict_flag=False,
    )
    
    # 4. Save visit
    save_visit(
        patient_id=patient_id,
        transcript=transcript,
        image_summary=image_summary,
        fusion_result=fusion_result,
        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
    )
    
    return {
        "fusion_result": fusion_result,
        "action_result": action_result,
        "history_summary": history_summary,
    }
```

**Explanation:**
- **Step 1:** Patient history fetch karta hai
- **Step 2:** `fuse()` function call karta hai (main fusion logic)
- **Step 3:** Confidence calculate karke triage decision leta hai
- **Step 4:** Current visit ko database mein save karta hai
- Complete result return karta hai

---

## Phase 4: Medical Assessment (चिकित्सा मूल्यांकन)

### Step 4.1: Fusion Service

**File: `app/services/fusion_service.py` (Lines 267-365)**
```python
def fuse(
    image_summary: str,
    image_conf: Optional[float],
    transcript: str,
    transcript_conf: Optional[float],
    history_summary: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    # Normalize confidences
    img_conf_n = _normalise_conf(image_conf)
    txt_conf_n = _normalise_conf(transcript_conf)
    
    # If no LLM, use fallback
    if llm_client is None:
        return _fallback_plan(...)
    
    # Build prompt
    prompt = build_medical_agent_prompt(
        image_summary=image_summary,
        transcript=transcript,
        history_summary=history_summary,
    )
    
    # Call LLM
    try:
        raw_output = llm_client.generate(prompt)
        parsed = json.loads(str(raw_output))
    except Exception as e:
        # Fallback on error
        return _fallback_plan(...)
    
    # Validate and return
    fallback = _fallback_plan(...)
    result = {
        "preliminary_diagnosis": parsed.get("preliminary_diagnosis") or fallback["preliminary_diagnosis"],
        "reasoning": parsed.get("reasoning") or fallback["reasoning"],
        "recommended_treatment": parsed.get("recommended_treatment") or fallback["recommended_treatment"],
        "medicine_constituents": parsed.get("medicine_constituents") or fallback["medicine_constituents"],
        "safety_notes": parsed.get("safety_notes") or fallback["safety_notes"],
        "fusion_confidence": fallback["fusion_confidence"],
        "llm_raw_output": raw_output,
        "simple_findings": fallback["simple_findings"],
    }
    return result
```

**Explanation:**
- **LLM Mode:** Agar LLM client ho, toh advanced diagnosis generate karta hai
- **Fallback Mode:** Agar LLM na ho, toh deterministic heuristics use karta hai
- **Error Handling:** Agar LLM fail ho, toh automatically fallback use hota hai
- **Validation:** Missing fields ko fallback se fill karta hai

### Step 4.2: LLM Prompt Building

**File: `app/prompts/medical_agent_prompt.py` (Lines 156-179)**
```python
def build_medical_agent_prompt(
    image_summary: str,
    transcript: str,
    history_summary: Optional[str] = None,
) -> str:
    history_summary = history_summary or "No significant prior history is available."
    
    return MEDICAL_AGENT_PROMPT_TEMPLATE.format(
        image_summary=image_summary.strip() or "No image was provided.",
        transcript=transcript.strip() or "The patient did not say anything.",
        history_summary=history_summary.strip(),
    )
```

**Explanation:**
- Detailed medical prompt template use karta hai
- Image summary, transcript, aur history ko prompt mein insert karta hai
- LLM ko comprehensive context deta hai

**Prompt Template Includes:**
- Role definition (medical expert)
- Diagnostic requirements
- Medication specifications
- Output format (JSON)
- Quality standards

### Step 4.3: LLM Response Generation

**File: `brain_of_the_doctor.py` (Lines 60-121)**
```python
def generate(self, prompt: str) -> str:
    try:
        # Try JSON mode
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a medical expert. Always respond with valid JSON only..."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
    except Exception:
        # Fallback without JSON mode
        chat_completion = self.client.chat.completions.create(...)
    
    response = chat_completion.choices[0].message.content
    
    # Clean markdown code blocks
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    
    return response.strip()
```

**Explanation:**
- Groq API ko prompt bhejta hai
- JSON mode try karta hai (agar supported ho)
- Response clean karta hai (markdown blocks remove)
- Pure JSON string return karta hai

**Example Response:**
```json
{
  "preliminary_diagnosis": "Plantar wart (verruca) on the foot",
  "reasoning": "The image shows characteristic black dots and rough surface...",
  "recommended_treatment": "LIKELY CONDITION:\nPlantar wart...\n\nCARE INSTRUCTIONS:\n1. Apply Salicylic Acid...",
  "medicine_constituents": ["Salicylic Acid (15-40%) - Topical solution/gel", ...],
  "safety_notes": "WARNING SIGNS — SEEK CARE IF:\n- Wart spreads rapidly..."
}
```

### Step 4.4: Fallback Plan (Offline Mode)

**File: `app/services/fusion_service.py` (Lines 62-264)**
```python
def _fallback_plan(...):
    combined_text = " ".join(filter(None, [image_summary, transcript]))
    findings = _extract_simple_findings(combined_text)
    
    # Check for specific conditions
    if findings["blister"] or (findings["foot"] and "blister" in combined_text.lower()):
        preliminary_diagnosis = "Friction blister on the plantar aspect of the foot..."
        recommended_treatment = "LIKELY CONDITION:\nFriction blister...\n\nCARE INSTRUCTIONS:\n1. Avoid popping..."
        medicine_constituents = ["Petroleum Jelly - Occlusive barrier...", ...]
    elif findings["wart"] or (findings["foot"] and "wart" in combined_text.lower()):
        preliminary_diagnosis = "Plantar wart (verruca) on the foot..."
        recommended_treatment = "LIKELY CONDITION:\nPlantar wart...\n\nCARE INSTRUCTIONS:\n1. Apply Salicylic Acid..."
        medicine_constituents = ["Salicylic Acid (15-40%) - Topical solution/gel", ...]
    # ... more conditions
    
    return {
        "preliminary_diagnosis": preliminary_diagnosis,
        "reasoning": reasoning,
        "recommended_treatment": recommended_treatment,
        "medicine_constituents": medicine_constituents,
        "safety_notes": safety_notes,
        "fusion_confidence": fusion_confidence,
        "llm_raw_output": None,
        "simple_findings": findings,
    }
```

**Explanation:**
- Keyword-based condition detection
- Pre-defined treatment plans
- Conservative approach (safety first)
- LLM ke bina bhi kaam karta hai

---

## Phase 5: Result Generation (परिणाम जनरेशन)

### Step 5.1: Confidence Calculation

**File: `app/services/confidence_service.py` (Lines 22-70)**
```python
def compute_action(
    fusion_conf: float,
    image_conf: Optional[float],
    transcript_conf: Optional[float],
    fused_findings: Optional[Dict[str, Any]],
    conflict_flag: bool = False,
) -> Dict[str, Any]:
    low_th = _get_threshold("FUSION_CONFIDENCE_LOW", 0.55)
    high_th = _get_threshold("FUSION_CONFIDENCE_HIGH", 0.8)
    
    # Normalize confidences
    img_c = _norm(image_conf)
    txt_c = _norm(transcript_conf)
    
    # Average all signals
    signals = [fusion_conf, img_c, txt_c]
    final_conf = sum(signals) / len(signals)
    
    # Triage decision
    if final_conf >= high_th and not conflict_flag:
        triage_action = "self_care_and_routine_followup"
    elif final_conf >= low_th:
        triage_action = "monitor_closely_and_seek_care_if_worse"
    else:
        triage_action = "recommend_in_person_review"
    
    return {
        "final_confidence": round(final_conf, 2),
        "triage_action": triage_action,
    }
```

**Explanation:**
- Sabhi confidence scores ko average karta hai
- Thresholds compare karta hai
- Triage action decide karta hai:
  - **High (≥0.8):** Self-care
  - **Medium (≥0.55):** Monitor closely
  - **Low (<0.55):** In-person review

### Step 5.2: Text Formatting

**File: `gradio_app.py` (Lines 26-40)**
```python
def _format_doctor_text(fusion_result, action_result):
    diag = fusion_result.get("preliminary_diagnosis", "")
    plan = fusion_result.get("recommended_treatment", "")
    safety = fusion_result.get("safety_notes", "")
    triage = action_result.get("triage_action", "monitor_closely_and_seek_care_if_worse")
    
    return (
        f"{diag} {plan} "
        f"Please also keep in mind: {safety} "
        f"(Overall suggestion: {triage.replace('_', ' ')}.)"
    )
```

**Explanation:**
- Diagnosis, treatment, safety notes ko combine karta hai
- Patient-friendly format mein return karta hai

### Step 5.3: Voice Generation

**File: `gradio_app.py` (Lines 95-101)**
```python
audio_output_path = None
try:
    audio_output_path = text_to_speech_with_elevenlabs(
        input_text=doctor_text, 
        output_filepath="final.mp3"
    )
except Exception:
    audio_output_path = None
```

**File: `voice_of_the_doctor.py` (Lines 28-64)**
```python
def text_to_speech_with_elevenlabs(input_text, output_filepath):
    # Try ElevenLabs first
    if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here":
        try:
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio = client.text_to_speech.convert(
                voice_id="UzYWd2rD2PPFPjXRG3Ul",  # Aria voice
                output_format="mp3_22050_32",
                text=input_text,
                model_id="eleven_turbo_v2"
            )
            with open(output_filepath, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            return output_filepath
        except Exception as e:
            print(f"ElevenLabs TTS failed: {e}. Falling back to gTTS...")
    
    # Fallback to gTTS
    try:
        audioobj = gTTS(text=input_text, lang="en", slow=False)
        audioobj.save(output_filepath)
        return output_filepath
    except Exception as e:
        print(f"gTTS also failed: {e}")
        return None
```

**Explanation:**
- Pehle ElevenLabs try karta hai (premium quality)
- Agar fail ho, toh gTTS use karta hai (free)
- Audio file save karta hai
- File path return karta hai

### Step 5.4: UI Display

**File: `gradio_app.py` (Lines 103-114)**
```python
return (
    transcript,
    doctor_text,
    treatment,
    medicine,
    safety_notes,
    action_result.get("final_confidence", 0.0),
    action_result.get("triage_action", ""),
    new_state["chat_history"],
    audio_output_path,
    new_state,
)
```

**Explanation:**
- Sabhi results UI ko return karta hai
- UI fields update hote hain:
  - Transcript
  - Doctor response
  - Treatment plan
  - Medicine constituents
  - Safety notes
  - Confidence score
  - Triage action
  - Chat history
  - Voice output

---

## Phase 6: Chat Functionality (चैट फंक्शनैलिटी)

### Step 6.1: Chat Initialization

**File: `gradio_app.py` (Lines 67-92)**
```python
new_state["initial_assessment"] = {
    "diagnosis": fusion_result.get("preliminary_diagnosis", ""),
    "treatment": fusion_result.get("recommended_treatment", ""),
    "medicine": fusion_result.get("medicine_constituents", []),
    "safety": fusion_result.get("safety_notes", ""),
    "reasoning": fusion_result.get("reasoning", ""),
    "image_summary": new_state.get("image_summary", ""),
    "transcript": transcript,
}

initial_greeting = (
    f"Hello! I've completed my initial assessment of your case.\n\n"
    f"**Diagnosis:** {fusion_result.get('preliminary_diagnosis', 'Assessment completed')}\n\n"
    ...
)
new_state["chat_history"] = [["", initial_greeting]]
```

**Explanation:**
- Initial assessment ko session state mein store karta hai
- Doctor ka greeting message banata hai
- Chat history initialize karta hai

### Step 6.2: Chat Callback

**File: `gradio_app.py` (Lines 117-193)**
```python
def chat_callback(message, chat_history, session_state):
    if not message or not message.strip():
        return chat_history, session_state
    
    if not session_state or not session_state.get("initial_assessment"):
        chat_history.append([message, "Please first submit..."])
        return chat_history, session_state
    
    # Get LLM client
    llm_client = _get_llm_client()
    
    # Build context
    initial = session_state["initial_assessment"]
    conversation_context = ""
    if len(chat_history) > 1:
        conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
        for user_msg, doctor_msg in chat_history[:-1]:
            conversation_context += f"Patient: {user_msg}\nDoctor: {doctor_msg}\n\n"
    
    # Build prompt
    context = f"""You are a professional, experienced medical doctor...
    INITIAL ASSESSMENT CONTEXT:
    - Diagnosis: {initial.get('diagnosis', 'Not specified')}
    - Treatment Plan: {initial.get('treatment', 'Not specified')}
    ...
    PATIENT'S CURRENT QUESTION:
    {message}
    ...
    """
    
    # Generate response
    if llm_client:
        doctor_response = llm_client.generate(context)
        # Clean JSON if needed
    else:
        doctor_response = f"Based on your initial assessment..."
    
    # Update chat history
    chat_history.append([message, doctor_response])
    session_state["chat_history"] = chat_history
    
    return chat_history, session_state
```

**Explanation:**
- User message receive karta hai
- Initial assessment context build karta hai
- Conversation history include karta hai
- LLM se response generate karta hai
- Chat history update karta hai

---

## Complete Code Flow (पूरा कोड फ्लो)

### End-to-End Flow

```
1. User opens UI (gradio_app.py launches)
   ↓
2. User records audio / uploads image
   ↓
3. User clicks "Analyze" button
   ↓
4. submit_callback() called (gradio_app.py)
   ↓
5. api_local.submit_record() called (app/api_local.py)
   ↓
6. Parallel Processing:
   ├─ Thread 1: transcribe_audio() → voice_of_the_patient.py
   │            → Groq Whisper API → transcript text
   └─ Thread 2: analyze_image() → brain_of_the_doctor.py
                → Groq Vision API → image summary
   ↓
7. get_multimodal_assessment() called (brain_of_the_doctor.py)
   ├─ get_history_summary() → history_service.py
   ├─ fuse() → fusion_service.py
   │   ├─ build_medical_agent_prompt() → medical_agent_prompt.py
   │   ├─ llm_client.generate() → Groq LLM API
   │   └─ Parse JSON response
   ├─ compute_action() → confidence_service.py
   └─ save_visit() → history_service.py
   ↓
8. Results formatted (gradio_app.py)
   ├─ _format_doctor_text()
   └─ text_to_speech_with_elevenlabs() → voice_of_the_doctor.py
   ↓
9. UI updates with results
   ↓
10. User can chat (chat_callback)
    ├─ Build context from initial assessment
    ├─ LLM generate response
    └─ Update chat history
```

---

## Key Features Summary (मुख्य विशेषताएं)

1. **Multimodal Input** - Audio + Image support
2. **Parallel Processing** - Fast execution (40-50% faster)
3. **LLM Integration** - Advanced medical diagnosis
4. **Offline Fallback** - Works without LLM
5. **History Management** - Patient visit tracking
6. **Real-time Chat** - Interactive consultation
7. **Voice Output** - Audio responses
8. **Error Resilience** - Multiple fallback layers

---

## Configuration (कॉन्फ़िगरेशन)

### Required Environment Variables (.env file)

```env
GROQ_API_KEY="your_groq_api_key_here"
ELEVENLABS_API_KEY="your_elevenlabs_api_key_here"  # Optional
FUSION_CONFIDENCE_LOW=0.55
FUSION_CONFIDENCE_HIGH=0.8
PATIENT_HISTORY_DB=patient_history.db
```

### Model Selection

**Speed Priority:**
- LLM: `llama-3.3-70b-versatile`
- STT: `whisper-large-v3-turbo`
- Vision: `llama-3.2-90b-vision-preview`

**Accuracy Priority:**
- LLM: `meta-llama/llama-4-maverick-17b-128e-instruct`
- STT: `whisper-large-v3`
- Vision: `llama-3.2-90b-vision-preview`

---

## Performance Optimizations (Performance सुधार)

1. **Parallel Processing** - Audio + Image simultaneously
2. **Fast Models** - Turbo variants use
3. **Token Limits** - max_tokens set (faster responses)
4. **Timeout Settings** - 30s timeout (faster failure)
5. **Caching** - Session state maintain

---

## Error Handling Strategy (Error Handling रणनीति)

1. **API Key Missing** - Fallback mode
2. **API Failure** - Automatic fallback
3. **JSON Parse Error** - Fallback plan use
4. **Thread Failure** - Default values use
5. **TTS Failure** - Silent failure (optional feature)

---

## Conclusion (निष्कर्ष)

Yeh system ek complete multimodal medical AI agent hai jo:
- Multiple input types handle karta hai
- Advanced LLM se diagnosis generate karta hai
- Offline mode support karta hai
- Real-time interaction provide karta hai
- Patient history maintain karta hai

Sabhi components modular hain aur independently test kar sakte hain. System robust hai aur multiple fallback mechanisms ke saath error resilience provide karta hai.

