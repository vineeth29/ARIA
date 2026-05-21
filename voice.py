import os, sys, threading, tempfile, wave, struct, time

_ENABLED = False
_RECORDING = False
_LISTEN_THREAD = None

def is_available():
    try:
        import faster_whisper
        import pyaudio
        return True
    except ImportError:
        return False

def install_deps():
    import subprocess
    pkgs = ["faster-whisper", "pyaudio"]
    for pkg in pkgs:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                       capture_output=True)

_model = None
def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _model

def record_until_silence(max_seconds=10, silence_threshold=500, silence_duration=1.5):
    import pyaudio
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)
    frames = []
    silent_chunks = 0
    required_silent = int(RATE / CHUNK * silence_duration)
    started = False
    start_time = time.time()
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        amplitude = max(struct.unpack(f"{CHUNK}h", data))
        if amplitude > silence_threshold:
            started = True
            silent_chunks = 0
        elif started:
            silent_chunks += 1
        if started and silent_chunks >= required_silent:
            break
        if time.time() - start_time > max_seconds:
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
    return tmp_path

def transcribe(audio_path):
    model = _get_model()
    segments, _ = model.transcribe(audio_path, beam_size=1, language="en")
    text = " ".join(s.text for s in segments).strip()
    os.unlink(audio_path)
    return text

def listen_once(status_cb=None):
    if not is_available():
        return None, "Voice not available. Run: pip install faster-whisper pyaudio"
    if status_cb:
        status_cb("Listening...")
    try:
        audio_path = record_until_silence()
        if status_cb:
            status_cb("Transcribing...")
        text = transcribe(audio_path)
        return text, None
    except Exception as e:
        return None, str(e)

def speak(text):
    import subprocess
    try:
        subprocess.Popen(
            ["powershell", "-c",
             f"Add-Type -AssemblyName System.Speech; "
             f"$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
             f"$s.Rate=1; $s.Speak('{text[:300]}')"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
