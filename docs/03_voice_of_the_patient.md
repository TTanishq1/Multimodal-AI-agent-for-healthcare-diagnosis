# Voice of the Patient Documentation (voice_of_the_patient.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`voice_of_the_patient.py` yeh file audio recording aur speech-to-text (STT) transcription handle karti hai. Patient ki voice ko text mein convert karti hai jo baad mein analysis ke liye use hoti hai.

### Main Responsibilities (मुख्य जिम्मेदारियां)

1. **Audio Recording** - Microphone se audio record karna
2. **Speech Transcription** - Audio ko text mein convert karna (Groq Whisper API use karke)

---

## Line-by-Line Code Explanation

### Lines 1-3: Environment Setup
```python
# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()
```
**Explanation:**
- `.env` file se environment variables load karta hai
- API keys access karne ke liye zaroori hai

### Lines 5-12: Audio Recording Setup
```python
#Step1: Setup Audio recorder (ffmpeg & portaudio)
# ffmpeg, portaudio, pyaudio
import logging
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```
**Explanation:**
- `logging` - Logs ke liye (debugging mein help karta hai)
- `speech_recognition` - Audio recording ke liye library
- `pydub` - Audio format conversion ke liye
- `BytesIO` - In-memory audio data handle karne ke liye
- Logging configure karta hai INFO level par

### Lines 14-43: Audio Recording Function
```python
def record_audio(file_path, timeout=20, phrase_time_limit=None):
    """
    Simplified function to record audio from the microphone and save it as an MP3 file.
    ...
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.info("Start speaking now...")
            
            # Record the audio
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Recording complete.")
            
            # Convert the recorded audio to an MP3 file
            wav_data = audio_data.get_wav_data()
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
            audio_segment.export(file_path, format="mp3", bitrate="128k")
            
            logging.info(f"Audio saved to {file_path}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
```
**Explanation:**
- `record_audio()` - Microphone se audio record karta hai
- `sr.Recognizer()` - Speech recognition object banata hai
- `sr.Microphone()` - Microphone access karta hai
- `adjust_for_ambient_noise()` - Background noise ko adjust karta hai (1 second)
- `listen()` - Audio record karta hai (timeout aur phrase_time_limit ke saath)
- `get_wav_data()` - WAV format mein audio data leta hai
- `AudioSegment.from_wav()` - WAV ko AudioSegment mein convert karta hai
- `export()` - MP3 format mein save karta hai (128k bitrate)
- Error handling - Agar koi problem aaye toh log karta hai

**Note:** Yeh function currently commented out hai (line 46) kyunki Gradio app directly audio file receive karti hai.

### Lines 45-46: Test Audio File
```python
audio_filepath="patient_voice_test_for_patient.mp3"
#record_audio(file_path=audio_filepath)
```
**Explanation:**
- Test file path define karta hai
- Recording function commented hai (testing ke liye)

### Lines 48-64: Old Transcription Code (Commented)
```python
'''
import os 
from groq import Groq
GROQ_API_KEY=os.environ.get("GROQ_API_KEY")
client=Groq(api_key=GROQ_API_KEY)
stt_model="whisper-large-v3-turbo"
audio_file=open(audio_filepath, "rb")

transcription=client.audio.transcriptions.create(
    model=stt_model,
    file=audio_file,
    language="en"
)

print(transcription.text)
'''
```
**Explanation:**
- Purana code jo directly transcription karta tha
- Ab function mein wrap kiya gaya hai

### Lines 66-82: Main Transcription Function
```python
import os
from groq import Groq

GROQ_API_KEY=os.environ.get("GROQ_API_KEY")
stt_model="whisper-large-v3-turbo"

def transcribe_with_groq(stt_model, audio_filepath, GROQ_API_KEY):
    client=Groq(api_key=GROQ_API_KEY)
    
    audio_file=open(audio_filepath, "rb")
    transcription=client.audio.transcriptions.create(
        model=stt_model,
        file=audio_file,
        language="en"
    )

    return transcription.text
```
**Explanation:**
**Line 69:** API key environment se fetch karta hai
```python
GROQ_API_KEY=os.environ.get("GROQ_API_KEY")
```

**Line 70:** STT model name define karta hai
```python
stt_model="whisper-large-v3-turbo"
```
- `whisper-large-v3-turbo` - Fast aur accurate transcription model

**Line 72:** Function definition
```python
def transcribe_with_groq(stt_model, audio_filepath, GROQ_API_KEY):
```
- Parameters:
  - `stt_model` - Model name (e.g., "whisper-large-v3-turbo")
  - `audio_filepath` - Audio file ka path
  - `GROQ_API_KEY` - API key for authentication

**Line 73:** Groq client banata hai
```python
client=Groq(api_key=GROQ_API_KEY)
```

**Line 75:** Audio file open karta hai
```python
audio_file=open(audio_filepath, "rb")
```
- `"rb"` - Read binary mode (audio files binary hote hain)

**Lines 76-80:** Transcription API call
```python
transcription=client.audio.transcriptions.create(
    model=stt_model,
    file=audio_file,
    language="en"
)
```
- Groq API ko audio file bhejta hai
- `model` - Whisper model specify karta hai
- `file` - Audio file object
- `language="en"` - English language specify karta hai

**Line 82:** Transcribed text return karta hai
```python
return transcription.text
```

---

## Workflow (काम कैसे होता है)

1. **Audio Input** - User microphone se audio record karta hai (Gradio UI se)
2. **File Save** - Audio file temporarily save hoti hai
3. **API Call** - Groq Whisper API ko audio file bheji jati hai
4. **Transcription** - API audio ko text mein convert karti hai
5. **Return Text** - Transcribed text return hota hai jo analysis ke liye use hota hai

---

## Model Options (Model Choices)

- **whisper-large-v3-turbo** (Current) - Fast aur accurate
- **whisper-large-v3** - More accurate but slower
- **whisper-medium** - Balanced speed/accuracy
- **whisper-small** - Fastest but less accurate

---

## Error Handling (Error कैसे Handle होते हैं)

Currently function mein explicit error handling nahi hai, lekin:
- Agar API key invalid ho, toh `api_local.py` mein catch hota hai
- Agar file open na ho, toh exception raise hoga
- Agar API call fail ho, toh fallback message return hota hai

---

## Dependencies (जरूरी Libraries)

- `groq` - Groq API client
- `speech_recognition` - Audio recording (optional, currently not used)
- `pydub` - Audio format conversion (optional)

---

## Usage Example (कैसे Use करें)

```python
from voice_of_the_patient import transcribe_with_groq
import os

# API key set karein
api_key = os.environ.get("GROQ_API_KEY")

# Audio file transcribe karein
transcript = transcribe_with_groq(
    stt_model="whisper-large-v3-turbo",
    audio_filepath="patient_audio.mp3",
    GROQ_API_KEY=api_key
)

print(transcript)  # "I have a wart on my foot"
```

---

## Integration (कहाँ Use होता है)

Yeh function `app/api_local.py` mein use hoti hai:
```python
transcript = transcribe_with_groq(
    GROQ_API_KEY=api_key,
    audio_filepath=audio_filepath,
    stt_model="whisper-large-v3-turbo",
)
```

---

## Performance Tips (Performance के लिए Tips)

1. **Model Selection** - `whisper-large-v3-turbo` fast aur accurate hai
2. **File Format** - MP3 format recommended hai (compressed)
3. **Audio Quality** - Clear audio se better transcription milti hai
4. **Language** - English specify karne se accuracy improve hoti hai

