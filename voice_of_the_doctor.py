"""
Text-to-speech functionality for the medical AI agent.
Supports ElevenLabs (premium) and gTTS (free fallback).
"""

import os
from gtts import gTTS
from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def text_to_speech_with_gtts(input_text, output_filepath):
    """
    Generate speech using gTTS (Google Text-to-Speech).
    Free, no API key required.
    """
    language = "en"
    audioobj = gTTS(
        text=input_text,
        lang=language,
        slow=False
    )
    audioobj.save(output_filepath)
    return output_filepath


def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """
    Generate speech using ElevenLabs, fallback to gTTS if API key is missing.
    Returns the output filepath for Gradio to use.
    """
    # Try ElevenLabs first if API key is available
    if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here":
        try:
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
            # Use the new text_to_speech.convert() method
            audio = client.text_to_speech.convert(
                voice_id="UzYWd2rD2PPFPjXRG3Ul",  # Aria voice ID
                output_format="mp3_22050_32",
                text=input_text,
                model_id="eleven_turbo_v2"
            )
            
            # Save the audio using chunks
            with open(output_filepath, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            return output_filepath
        except Exception as e:
            print(f"ElevenLabs TTS failed: {e}. Falling back to gTTS...")
    
    # Fallback to gTTS (free, no API key needed)
    try:
        language = "en"
        audioobj = gTTS(text=input_text, lang=language, slow=False)
        # Save as MP3 (gTTS supports MP3)
        audioobj.save(output_filepath)
        return output_filepath
    except Exception as e:
        print(f"gTTS also failed: {e}")
        return None
