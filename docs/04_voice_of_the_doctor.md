# Voice of the Doctor Documentation (voice_of_the_doctor.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`voice_of_the_doctor.py` yeh file text-to-speech (TTS) functionality provide karti hai. Doctor ka text response ko audio mein convert karti hai taaki patient audio sun sake.

### Main Responsibilities (मुख्य जिम्मेदारियां)

1. **ElevenLabs TTS** - Premium voice synthesis (agar API key ho)
2. **gTTS Fallback** - Free Google TTS (agar ElevenLabs na ho)

---

## Line-by-Line Code Explanation

### Lines 1-4: Module Description
```python
"""
Text-to-speech functionality for the medical AI agent.
Supports ElevenLabs (premium) and gTTS (free fallback).
"""
```
**Explanation:**
- File ka purpose explain karta hai
- Dono TTS options mention karta hai

### Lines 6-10: Imports and API Key
```python
import os
from gtts import gTTS
from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
```
**Explanation:**
- `os` - Environment variables access karne ke liye
- `gTTS` - Google Text-to-Speech library (free)
- `ElevenLabs` - Premium TTS service client
- `ELEVENLABS_API_KEY` - Environment se API key fetch karta hai

### Lines 13-25: gTTS Function
```python
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
```
**Explanation:**
- `text_to_speech_with_gtts()` - Free TTS function
- `language = "en"` - English language specify karta hai
- `gTTS()` - Google TTS object banata hai
  - `text` - Text jo convert karna hai
  - `lang` - Language code
  - `slow=False` - Normal speed (agar `True` ho toh slow)
- `save()` - Audio file save karta hai
- File path return karta hai

### Lines 28-64: ElevenLabs Function (with Fallback)
```python
def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """
    Generate speech using ElevenLabs, fallback to gTTS if API key is missing.
    Returns the output filepath for Gradio to use.
    """
```
**Explanation:**
Yeh main function hai jo pehle ElevenLabs try karti hai, phir gTTS use karti hai.

**Lines 34-51: ElevenLabs Try Block**
```python
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
```
**Explanation:**
**Line 34:** API key check karta hai
```python
if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here":
```
- Agar valid API key ho, toh ElevenLabs use karta hai

**Line 36:** ElevenLabs client banata hai
```python
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
```

**Lines 39-44:** TTS API call
```python
audio = client.text_to_speech.convert(
    voice_id="UzYWd2rD2PPFPjXRG3Ul",  # Aria voice ID
    output_format="mp3_22050_32",
    text=input_text,
    model_id="eleven_turbo_v2"
)
```
- `voice_id` - Voice selection (Aria - natural female voice)
- `output_format` - MP3 format, 22050 Hz, 32 kbps
- `text` - Text jo convert karna hai
- `model_id` - Fast model use karta hai (`eleven_turbo_v2`)

**Lines 47-50:** Audio Save
```python
with open(output_filepath, "wb") as f:
    for chunk in audio:
        f.write(chunk)
```
- Audio chunks ko file mein write karta hai
- `"wb"` - Write binary mode

**Line 52:** Success par file path return karta hai

**Line 53:** Error handling - Agar fail ho, toh gTTS fallback use hoga

**Lines 55-64: gTTS Fallback**
```python
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
```
**Explanation:**
- Agar ElevenLabs fail ho ya API key na ho, toh gTTS use karta hai
- Free hai, koi API key nahi chahiye
- Agar dono fail ho jayein, toh `None` return karta hai

---

## Workflow (काम कैसे होता है)

1. **Function Call** - `text_to_speech_with_elevenlabs()` call hoti hai
2. **API Key Check** - ElevenLabs API key check hoti hai
3. **ElevenLabs Try** - Agar key ho, toh premium TTS use hota hai
4. **gTTS Fallback** - Agar fail ho, toh free gTTS use hota hai
5. **File Save** - Audio file save hoti hai
6. **Return Path** - File path return hota hai jo UI mein play hota hai

---

## Voice Options (Voice Choices)

### ElevenLabs Voices
- **Aria** (Current) - Natural female voice
- Other voices available via different `voice_id`

### gTTS
- Default English voice (no customization)

---

## Audio Formats (Audio Formats)

- **ElevenLabs**: `mp3_22050_32` - MP3, 22kHz, 32kbps
- **gTTS**: MP3 format (default)

---

## Error Handling (Error कैसे Handle होते हैं)

1. **No API Key** - Directly gTTS use hota hai
2. **ElevenLabs Failure** - Automatically gTTS fallback
3. **gTTS Failure** - `None` return hota hai (UI handle karti hai)
4. **File Write Error** - Exception catch hota hai

---

## Dependencies (जरूरी Libraries)

- `elevenlabs` - Premium TTS service (optional)
- `gtts` - Google Text-to-Speech (required for fallback)

---

## Usage Example (कैसे Use करें)

```python
from voice_of_the_doctor import text_to_speech_with_elevenlabs

# Text ko audio mein convert karein
audio_path = text_to_speech_with_elevenlabs(
    input_text="You have a plantar wart. Apply salicylic acid daily.",
    output_filepath="doctor_response.mp3"
)

if audio_path:
    print(f"Audio saved to {audio_path}")
    # Play audio file
else:
    print("TTS failed")
```

---

## Integration (कहाँ Use होता है)

Yeh function `gradio_app.py` mein use hoti hai:
```python
audio_output_path = text_to_speech_with_elevenlabs(
    input_text=doctor_text, 
    output_filepath="final.mp3"
)
```

---

## Performance Tips (Performance के लिए Tips)

1. **ElevenLabs** - Better quality, faster (agar API key ho)
2. **gTTS** - Free but slower, lower quality
3. **Model Selection** - `eleven_turbo_v2` fast hai
4. **File Format** - MP3 compressed format use karein

---

## Cost Considerations (Cost के बारे में)

- **ElevenLabs** - Paid service (per character cost)
- **gTTS** - Completely free
- Recommendation: Development ke liye gTTS, production ke liye ElevenLabs

