
# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()

import os

import gradio as gr

from app import api_local
from brain_of_the_doctor import GroqLLMClient
from voice_of_the_doctor import text_to_speech_with_elevenlabs


def _get_llm_client():
    """Create LLM client if API key is available, otherwise return None."""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            return GroqLLMClient(api_key=api_key)
    except Exception as e:
        print(f"Could not create LLM client: {e}. Using fallback mode.")
    return None


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


def submit_callback(audio_filepath, image_filepath, patient_id, session_state):
    # Try to use LLM if available, otherwise use fallback
    llm_client = _get_llm_client()
    
    result = api_local.submit_record(
        audio_filepath=audio_filepath,
        image_filepath=image_filepath,
        patient_id=patient_id or None,
        llm_client=llm_client,  # Use LLM if available
    )

    transcript = result["transcript"]
    fusion_result = result["fusion_result"]
    action_result = result["action_result"]

    doctor_text = _format_doctor_text(fusion_result, action_result)
    treatment = fusion_result.get("recommended_treatment", "")
    medicine = ", ".join(fusion_result.get("medicine_constituents", []))
    safety_notes = fusion_result.get("safety_notes", "")

    # Update session state for chatbot conversation
    new_state = result["session_state"]
    
    # Store initial assessment in session state for chatbot context
    new_state["initial_assessment"] = {
        "diagnosis": fusion_result.get("preliminary_diagnosis", ""),
        "treatment": fusion_result.get("recommended_treatment", ""),
        "medicine": fusion_result.get("medicine_constituents", []),
        "safety": fusion_result.get("safety_notes", ""),
        "reasoning": fusion_result.get("reasoning", ""),
        "image_summary": new_state.get("image_summary", ""),
        "transcript": transcript,
    }
    
    # Initialize chat history with initial doctor greeting
    initial_greeting = (
        f"Hello! I've completed my initial assessment of your case.\n\n"
        f"**Diagnosis:** {fusion_result.get('preliminary_diagnosis', 'Assessment completed')}\n\n"
        f"I've prepared a treatment plan for you. You can see the details in the assessment results on the left.\n\n"
        f"Feel free to ask me any questions about:\n"
        f"• Your diagnosis and what it means\n"
        f"• How to follow the treatment plan\n"
        f"• Your medications and how to use them\n"
        f"• What symptoms to watch for\n"
        f"• When to seek additional care\n\n"
        f"How can I help you today?"
    )
    new_state["chat_history"] = [
        ["", initial_greeting]
    ]

    # Prepare voice output.
    audio_output_path = None
    try:
        audio_output_path = text_to_speech_with_elevenlabs(
            input_text=doctor_text, output_filepath="final.mp3"
        )
    except Exception:
        audio_output_path = None

    return (
        transcript,
        doctor_text,
        treatment,
        medicine,
        safety_notes,
        action_result.get("final_confidence", 0.0),
        action_result.get("triage_action", ""),
        new_state["chat_history"],  # Return chat history for chatbot
        audio_output_path,
        new_state,
    )


def chat_callback(message, chat_history, session_state):
    """Handle real-time chat with the doctor."""
    if not message or not message.strip():
        return chat_history, session_state
    
    if not session_state or not session_state.get("initial_assessment"):
        # No initial assessment yet, ask user to submit first
        chat_history.append([message, "Please first submit your medical image and/or audio description for analysis."])
        return chat_history, session_state
    
    # Get LLM client for chatbot responses
    llm_client = _get_llm_client()
    
    # Build context from initial assessment and conversation history
    initial = session_state["initial_assessment"]
    
    # Build conversation history string
    conversation_context = ""
    if len(chat_history) > 1:  # More than just the initial greeting
        conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
        for i, (user_msg, doctor_msg) in enumerate(chat_history[:-1], 1):  # Exclude current message
            conversation_context += f"Patient: {user_msg}\nDoctor: {doctor_msg}\n\n"
    
    context = f"""You are a professional, experienced medical doctor providing real-time assistance to a patient in a consultation.

INITIAL ASSESSMENT CONTEXT:
- Diagnosis: {initial.get('diagnosis', 'Not specified')}
- Treatment Plan: {initial.get('treatment', 'Not specified')}
- Medicine Constituents: {', '.join(initial.get('medicine', []))}
- Safety Notes: {initial.get('safety', 'Not specified')}
- Clinical Reasoning: {initial.get('reasoning', 'Not specified')}
- Image Findings: {initial.get('image_summary', 'No image provided')}
- Patient's Initial Description: {initial.get('transcript', 'No description provided')}
{conversation_context}
PATIENT'S CURRENT QUESTION:
{message}

INSTRUCTIONS:
1. Answer the patient's question based on the initial assessment context and conversation history above
2. Provide clear, professional medical guidance that is specific to their condition
3. Be empathetic, warm, and reassuring - speak as a caring doctor would
4. Reference the initial diagnosis and treatment plan when relevant
5. If asked about medications, explain how to use them properly, dosages, and what to expect
6. If asked about symptoms, relate them to the initial assessment and explain what they mean
7. If the question requires urgent medical attention, clearly state that and recommend immediate care
8. Keep responses concise but comprehensive (typically 2-5 sentences)
9. Use natural, conversational language - avoid overly technical jargon unless necessary
10. If you don't have enough information, ask clarifying questions or recommend in-person evaluation
11. Maintain continuity with previous conversation if relevant

Respond naturally as a doctor would in a real consultation, addressing the patient's concern directly:"""

    # Generate doctor's response
    doctor_response = ""
    if llm_client:
        try:
            doctor_response = llm_client.generate(context)
            # Clean up response if it's wrapped in JSON
            if doctor_response.startswith('{'):
                import json
                try:
                    parsed = json.loads(doctor_response)
                    doctor_response = parsed.get("response", parsed.get("answer", doctor_response))
                except:
                    pass
        except Exception as e:
            print(f"Error generating chat response: {e}")
            doctor_response = "I apologize, but I'm having trouble processing your question right now. Please try rephrasing it or consult with a healthcare provider in person if this is urgent."
    else:
        # Fallback response without LLM
        doctor_response = f"Based on your initial assessment showing {initial.get('diagnosis', 'your condition')}, I'd recommend following the treatment plan provided. For specific questions about your condition, please consult with a healthcare provider in person for the most accurate guidance."
    
    # Update chat history
    chat_history.append([message, doctor_response])
    session_state["chat_history"] = chat_history
    
    return chat_history, session_state


with gr.Blocks(title="AI Doctor with Vision and Voice") as iface:
    state = gr.State({})

    gr.Markdown("## 🏥 AI Doctor with Vision, Voice, and Real-Time Chat")

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources=["microphone"], type="filepath", label="🎤 Record Your Voice"
            )
            image_input = gr.Image(
                type="filepath", label="📷 Upload Medical Image (optional)"
            )
            patient_id = gr.Textbox(
                label="Patient ID (optional)",
                placeholder="e.g. patient123",
            )
            submit_btn = gr.Button("🔍 Analyze", variant="primary")
            
            gr.Markdown("### 📋 Initial Assessment Results")
            transcript_out = gr.Textbox(label="🗣️ Speech to Text", lines=2)
            doctor_out = gr.Textbox(label="👨‍⚕️ Doctor's Overall Response", lines=3)
            treatment_out = gr.Textbox(label="💊 Treatment Plan", lines=4)
            medicine_out = gr.Textbox(label="🧪 Medicine Constituents", lines=3)
            safety_out = gr.Textbox(label="⚠️ Safety Notes", lines=3)
            confidence_out = gr.Slider(
                0,
                1,
                value=0,
                step=0.01,
                label="Model Confidence (combined)",
                interactive=False,
            )
            triage_out = gr.Textbox(label="Triage Suggestion", interactive=False)
            voice_out = gr.Audio(label="🔊 Doctor's Voice Response")
        
        with gr.Column(scale=1):
            gr.Markdown("### 💬 Chat with Your Doctor")
            chatbot = gr.Chatbot(
                label="Real-Time Doctor Consultation",
                height=500,
                show_label=True,
            )
            chat_input = gr.Textbox(
                label="Type your question here",
                placeholder="Ask me anything about your condition, treatment, medications, or symptoms...",
                lines=2,
            )
            chat_btn = gr.Button("💬 Send Message", variant="primary")

    # Submit button - initial assessment
    submit_btn.click(
        fn=submit_callback,
        inputs=[audio_input, image_input, patient_id, state],
    outputs=[
            transcript_out,
            doctor_out,
            treatment_out,
            medicine_out,
            safety_out,
            confidence_out,
            triage_out,
            chatbot,  # Update chatbot with initial greeting
            voice_out,
            state,
        ],
    )
    
    # Chat button - real-time conversation
    chat_btn.click(
        fn=chat_callback,
        inputs=[chat_input, chatbot, state],
        outputs=[chatbot, state],
    ).then(
        lambda: "",  # Clear input after sending
        outputs=[chat_input],
    )
    
    # Allow Enter key to send message
    chat_input.submit(
        fn=chat_callback,
        inputs=[chat_input, chatbot, state],
        outputs=[chatbot, state],
    ).then(
        lambda: "",  # Clear input after sending
        outputs=[chat_input],
)

iface.launch(debug=True)

#http://127.0.0.1:7860

# now this is similar to above code only. just that clear button is removed and now doctor voice can also be played in UI itself along with attachment file is generated. 
'''
import os
import gradio as gr

from brain_of_the_doctor import encode_image, analyze_image_with_query
from voice_of_the_patient import transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs

system_prompt = """You have to act as a professional doctor, i know you are not but this is for learning purpose. 
            What's in this image?. Do you find anything wrong with it medically? 
            If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in 
            your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person.
            Donot say 'In the image I see' but say 'With what I see, I think you have ....'
            Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, 
            Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""

def process_inputs(audio_filepath, image_filepath):
    # Debug: Check if audio is captured
    print(f"Audio file received: {audio_filepath}")
    print(f"Image file received: {image_filepath}")
    
    # Handle audio input
    if audio_filepath is None:
        speech_to_text_output = "No audio recorded"
    else:
        try:
            speech_to_text_output = transcribe_with_groq(
                GROQ_API_KEY=os.environ.get("GROQ_API_KEY"), 
                audio_filepath=audio_filepath,
                stt_model="whisper-large-v3"
            )
        except Exception as e:
            speech_to_text_output = f"Error in transcription: {str(e)}"

    # Handle the image input
    if image_filepath:
        try:
            doctor_response = analyze_image_with_query(
                query=system_prompt + speech_to_text_output, 
                encoded_image=encode_image(image_filepath), 
                model="meta-llama/llama-4-scout-17b-16e-instruct"
            )
        except Exception as e:
            doctor_response = f"Error in image analysis: {str(e)}"
    else:
        doctor_response = "No image provided for me to analyze"

    # Generate voice response
    try:
        audio_output_path = "final_response.mp3"
        text_to_speech_with_elevenlabs(
            input_text=doctor_response, 
            output_filepath=audio_output_path
        )
        voice_of_doctor = audio_output_path
    except Exception as e:
        voice_of_doctor = None
        print(f"Error in TTS: {str(e)}")

    return speech_to_text_output, doctor_response, voice_of_doctor

# Create the interface
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(
            sources=["microphone"], 
            type="filepath",
            format="wav",
            label="🎤 Record Your Voice"
        ),
        gr.Image(
            type="filepath",
            label="📷 Upload Medical Image"
        )
    ],
    outputs=[
        gr.Textbox(label="🗣️ Speech to Text"),
        gr.Textbox(label="👨‍⚕️ Doctor's Response"),
        gr.Audio(label="🔊 Doctor's Voice Response")
    ],
    title="🏥 AI Doctor with Vision and Voice",
    description="Record your voice and upload an image for medical analysis"
)

iface.launch(debug=True)
'''




#Generated by claude. where in 
'''Separated recording from processing - Audio recording is now independent
Added explicit submit button - Processing only happens when you click "Analyze"
Added max_threads=10 - Allows concurrent operations
Removed automatic processing - Audio recording won't trigger processing

The root cause was likely that your original gr.Interface was trying to process the audio immediately when it was recorded, causing the server to be busy and interfering with the recording process.
Alternative quick fix for your original code:
Change your gr.Interface to process only on submit, not on input change:'''


'''
import os
import gradio as gr
from concurrent.futures import ThreadPoolExecutor
import threading

from brain_of_the_doctor import encode_image, analyze_image_with_query
from voice_of_the_patient import transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs

system_prompt = """You have to act as a professional doctor, i know you are not but this is for learning purpose. 
            What's in this image?. Do you find anything wrong with it medically? 
            If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in 
            your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person.
            Donot say 'In the image I see' but say 'With what I see, I think you have ....'
            Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, 
            Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""

def process_inputs(audio_filepath, image_filepath):
    # Debug: Check if audio is captured
    print(f"Audio file received: {audio_filepath}")
    print(f"Image file received: {image_filepath}")
    
    # Handle audio input
    if audio_filepath is None:
        speech_to_text_output = "No audio recorded"
    else:
        try:
            speech_to_text_output = transcribe_with_groq(
                GROQ_API_KEY=os.environ.get("GROQ_API_KEY"), 
                audio_filepath=audio_filepath,
                stt_model="whisper-large-v3"
            )
        except Exception as e:
            speech_to_text_output = f"Error in transcription: {str(e)}"

    # Handle the image input
    if image_filepath:
        try:
            doctor_response = analyze_image_with_query(
                query=system_prompt + speech_to_text_output, 
                encoded_image=encode_image(image_filepath), 
                model="meta-llama/llama-4-scout-17b-16e-instruct"
            )
        except Exception as e:
            doctor_response = f"Error in image analysis: {str(e)}"
    else:
        doctor_response = "No image provided for me to analyze"

    # Generate voice response
    try:
        audio_output_path = "final_response.mp3"
        text_to_speech_with_elevenlabs(
            input_text=doctor_response, 
            output_filepath=audio_output_path
        )
        voice_of_doctor = audio_output_path
    except Exception as e:
        voice_of_doctor = None
        print(f"Error in TTS: {str(e)}")

    return speech_to_text_output, doctor_response, voice_of_doctor

# Create interface with separated recording and processing
with gr.Blocks(title="AI Doctor with Vision and Voice") as iface:
    gr.Markdown("# 🏥 AI Doctor with Vision and Voice")
    gr.Markdown("Record your voice and upload an image for medical analysis")
    
    with gr.Row():
        with gr.Column():
            # Audio recording - separated from processing
            audio_input = gr.Audio(
                sources=["microphone"], 
                type="filepath",
                label="🎤 Record Your Voice"
            )
            
            image_input = gr.Image(
                type="filepath",
                label="📷 Upload Medical Image"
            )
            
            # Separate submit button
            submit_btn = gr.Button("🔍 Analyze", variant="primary")
        
        with gr.Column():
            speech_output = gr.Textbox(label="🗣️ Speech to Text")
            doctor_output = gr.Textbox(label="👨‍⚕️ Doctor's Response")
            voice_output = gr.Audio(label="🔊 Doctor's Voice Response")
    
    # Only process when submit is clicked, not when audio changes
    submit_btn.click(
        fn=process_inputs,
        inputs=[audio_input, image_input],
        outputs=[speech_output, doctor_output, voice_output]
    )

# Launch with specific settings to avoid blocking
iface.launch(
    debug=True,
    show_error=True,
    server_name="127.0.0.1",
    server_port=7860,
    max_threads=10  # Allow multiple concurrent requests
)
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(
            sources=["microphone"], 
            type="filepath",
            format="wav",
            label="🎤 Record Your Voice"
        ),
        gr.Image(
            type="filepath",
            label="📷 Upload Medical Image"
        )
    ],
    outputs=[
        gr.Textbox(label="🗣️ Speech to Text"),
        gr.Textbox(label="👨‍⚕️ Doctor's Response"),
        gr.Audio(label="🔊 Doctor's Voice Response")
    ],
    live=False,
    title="🏥 AI Doctor with Vision and Voice",
    description="Record your voice and upload an image for medical analysis"
)

iface.launch(debug=True)
'''
