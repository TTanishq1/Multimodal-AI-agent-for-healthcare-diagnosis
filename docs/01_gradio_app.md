# Gradio App Documentation (gradio_app.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`gradio_app.py` yeh main UI file hai jo user ko web interface provide karti hai. Isme Gradio library use hoti hai jo ek simple web interface banane mein help karti hai.

### Complete Workflow (पूरा काम कैसे होता है)

1. **Environment Setup** - `.env` file se API keys load hoti hain
2. **UI Creation** - Gradio Blocks se interface banaya jata hai
3. **User Input** - User audio/image submit karta hai
4. **Processing** - Backend services call hote hain
5. **Output Display** - Results UI mein show hote hain

---

## Line-by-Line Code Explanation

### Lines 1-4: Environment Setup
```python
# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()
```
**Explanation:**
- `dotenv` library `.env` file se environment variables load karti hai
- `load_dotenv()` function call se sabhi API keys environment mein set ho jati hain
- Yeh zaroori hai kyunki Groq API key `.env` file mein stored hoti hai

### Lines 6-12: Imports
```python
import os
import gradio as gr
from app import api_local
from brain_of_the_doctor import GroqLLMClient
from voice_of_the_doctor import text_to_speech_with_elevenlabs
```
**Explanation:**
- `os` - Operating system functions ke liye (environment variables access karne ke liye)
- `gradio as gr` - Web UI banane ke liye Gradio library
- `api_local` - Backend processing functions
- `GroqLLMClient` - LLM API calls ke liye client
- `text_to_speech_with_elevenlabs` - Text ko speech mein convert karne ke liye

### Lines 15-23: LLM Client Helper Function
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
- Yeh function LLM client banata hai agar API key available hai
- `os.environ.get("GROQ_API_KEY")` - Environment se API key fetch karta hai
- Agar key valid hai (placeholder nahi hai), toh `GroqLLMClient` banata hai
- Agar koi error aaye ya key na ho, toh `None` return karta hai (fallback mode)

### Lines 26-40: Text Formatting Function
```python
def _format_doctor_text(fusion_result, action_result):
    """Compose a concise, patient‑facing text answer."""
    if not fusion_result:
        return "I could not generate an assessment from the information provided."

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
- Yeh function doctor ka response format karta hai patient ke liye
- `fusion_result` se diagnosis, treatment, aur safety notes extract karta hai
- `action_result` se triage suggestion leta hai
- Sabko combine karke ek readable text banata hai
- `triage.replace('_', ' ')` - Underscores ko spaces mein convert karta hai

### Lines 43-114: Submit Callback Function
```python
def submit_callback(audio_filepath, image_filepath, patient_id, session_state):
```
**Explanation:**
Yeh main function hai jo user ke submit button click par call hota hai.

**Line 45:** LLM client banata hai (agar available ho)
```python
llm_client = _get_llm_client()
```

**Lines 47-52:** Backend processing call
```python
result = api_local.submit_record(
    audio_filepath=audio_filepath,
    image_filepath=image_filepath,
    patient_id=patient_id or None,
    llm_client=llm_client,
)
```
- `api_local.submit_record()` - Main processing function jo audio/image process karti hai
- Parallel processing se audio transcription aur image analysis dono simultaneously hote hain

**Lines 54-61:** Results extract karna
```python
transcript = result["transcript"]
fusion_result = result["fusion_result"]
action_result = result["action_result"]
doctor_text = _format_doctor_text(fusion_result, action_result)
treatment = fusion_result.get("recommended_treatment", "")
medicine = ", ".join(fusion_result.get("medicine_constituents", []))
safety_notes = fusion_result.get("safety_notes", "")
```
- Har result ko extract karke separate variables mein store karta hai
- Medicine constituents ko comma-separated string mein convert karta hai

**Lines 64-75:** Session state update
```python
new_state = result["session_state"]
new_state["initial_assessment"] = {
    "diagnosis": fusion_result.get("preliminary_diagnosis", ""),
    "treatment": fusion_result.get("recommended_treatment", ""),
    ...
}
```
- Session state mein initial assessment store karta hai
- Yeh baad mein chat functionality ke liye use hota hai

**Lines 78-92:** Chat initialization
```python
initial_greeting = (
    f"Hello! I've completed my initial assessment...\n\n"
    ...
)
new_state["chat_history"] = [["", initial_greeting]]
```
- Doctor ka initial greeting message banata hai
- Chat history initialize karta hai

**Lines 95-101:** Voice output generation
```python
try:
    audio_output_path = text_to_speech_with_elevenlabs(
        input_text=doctor_text, output_filepath="final.mp3"
    )
except Exception:
    audio_output_path = None
```
- Doctor ka text ko speech mein convert karta hai
- Agar error aaye toh `None` set karta hai (optional feature)

**Lines 103-114:** Return values
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
- Sabhi outputs return karta hai jo UI mein display honge

### Lines 117-193: Chat Callback Function
```python
def chat_callback(message, chat_history, session_state):
```
**Explanation:**
Yeh function real-time chat handle karta hai.

**Lines 119-125:** Validation
```python
if not message or not message.strip():
    return chat_history, session_state

if not session_state or not session_state.get("initial_assessment"):
    chat_history.append([message, "Please first submit..."])
    return chat_history, session_state
```
- Check karta hai ki message valid hai
- Check karta hai ki initial assessment ho chuka hai

**Lines 128-138:** Context building
```python
llm_client = _get_llm_client()
initial = session_state["initial_assessment"]
conversation_context = ""
if len(chat_history) > 1:
    conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
    for i, (user_msg, doctor_msg) in enumerate(chat_history[:-1], 1):
        conversation_context += f"Patient: {user_msg}\nDoctor: {doctor_msg}\n\n"
```
- Previous conversation history build karta hai
- Context banata hai jo LLM ko diya jayega

**Lines 140-167:** Prompt creation
```python
context = f"""You are a professional, experienced medical doctor...
INITIAL ASSESSMENT CONTEXT:
- Diagnosis: {initial.get('diagnosis', 'Not specified')}
...
PATIENT'S CURRENT QUESTION:
{message}
...
"""
```
- Complete prompt banata hai jo LLM ko context deta hai
- Initial assessment, conversation history, aur current question include karta hai

**Lines 170-187:** Response generation
```python
if llm_client:
    try:
        doctor_response = llm_client.generate(context)
        if doctor_response.startswith('{'):
            import json
            try:
                parsed = json.loads(doctor_response)
                doctor_response = parsed.get("response", parsed.get("answer", doctor_response))
            except:
                pass
    except Exception as e:
        doctor_response = "I apologize, but I'm having trouble..."
else:
    doctor_response = f"Based on your initial assessment..."
```
- LLM se response generate karta hai
- Agar JSON format mein aaye toh parse karta hai
- Fallback response agar LLM na ho

**Lines 190-193:** Chat history update
```python
chat_history.append([message, doctor_response])
session_state["chat_history"] = chat_history
return chat_history, session_state
```
- New message aur response ko chat history mein add karta hai

### Lines 196-282: UI Creation
```python
with gr.Blocks(title="AI Doctor with Vision and Voice") as iface:
    state = gr.State({})
```
**Explanation:**
- `gr.Blocks` - Main container jo UI elements ko organize karta hai
- `gr.State({})` - Session state maintain karta hai

**Lines 201-230:** Left Column (Input & Results)
```python
with gr.Column(scale=1):
    audio_input = gr.Audio(...)
    image_input = gr.Image(...)
    patient_id = gr.Textbox(...)
    submit_btn = gr.Button("🔍 Analyze", variant="primary")
    
    gr.Markdown("### 📋 Initial Assessment Results")
    transcript_out = gr.Textbox(...)
    doctor_out = gr.Textbox(...)
    ...
```
- Input fields: Audio recording, image upload, patient ID
- Output fields: Transcript, doctor response, treatment, medicine, safety notes, confidence, triage, voice output

**Lines 232-244:** Right Column (Chat)
```python
with gr.Column(scale=1):
    gr.Markdown("### 💬 Chat with Your Doctor")
    chatbot = gr.Chatbot(...)
    chat_input = gr.Textbox(...)
    chat_btn = gr.Button("💬 Send Message", variant="primary")
```
- Chat interface: Chatbot display, input box, send button

**Lines 247-262:** Submit Button Event
```python
submit_btn.click(
    fn=submit_callback,
    inputs=[audio_input, image_input, patient_id, state],
    outputs=[transcript_out, doctor_out, ...],
)
```
- Submit button click par `submit_callback` function call hota hai
- Inputs aur outputs specify kiye hain

**Lines 265-282:** Chat Button Events
```python
chat_btn.click(
    fn=chat_callback,
    inputs=[chat_input, chatbot, state],
    outputs=[chatbot, state],
).then(
    lambda: "",  # Clear input after sending
    outputs=[chat_input],
)
```
- Chat button aur Enter key dono se chat callback trigger hota hai
- Message send hone ke baad input box clear ho jata hai

### Line 284: Launch Application
```python
iface.launch(debug=True)
```
**Explanation:**
- Application start karta hai
- `debug=True` - Debug mode enable karta hai
- Default URL: `http://127.0.0.1:7860`

---

## Key Features (मुख्य विशेषताएं)

1. **Multimodal Input** - Audio aur image dono accept karta hai
2. **Real-time Chat** - Doctor se baat kar sakte hain
3. **Voice Output** - Doctor ka response audio mein bhi sun sakte hain
4. **Session Management** - Patient history maintain hoti hai
5. **Fallback Mode** - LLM na ho toh bhi kaam karta hai

---

## Dependencies (जरूरी Libraries)

- `gradio` - Web UI
- `dotenv` - Environment variables
- `app.api_local` - Backend processing
- `brain_of_the_doctor` - LLM client
- `voice_of_the_doctor` - Text-to-speech

---

## Usage (कैसे Use करें)

1. `.env` file mein `GROQ_API_KEY` set karein
2. Run karein: `python gradio_app.py`
3. Browser mein `http://127.0.0.1:7860` open karein
4. Audio record karein ya image upload karein
5. "Analyze" button click karein
6. Results dekhein aur chat karein

