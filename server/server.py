import os
import uuid
import time
import numpy as np
import ctranslate2
from flask import Flask, request, jsonify
import gigaam
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from utils.logging import get_logger

logger = get_logger('stt')

AUDIO_FILES_DIR = 'audio_files'



def load_model_once():
    global ru_model, en_model, lid_model

    logger.info("Loading LID model...")
    start_time = time.time()
    lid_model = WhisperModel(
        "weights/whisper_base",
        device="cuda",
        compute_type="float16",
    )
    logger.info(f"LID model loaded in  {time.time() - start_time:.2f} seconds")

    logger.info("Loading STT RU (GigaAM) model...")
    start_time = time.time()
    ru_model = gigaam.load_model(
        "v3_e2e_rnnt",
        fp16_encoder=True,
        use_flash=False,
        device='cuda',
        download_root='weights/gigaAM'
    )
    logger.info(f"STT RU model loaded in {time.time() - start_time:.2f} seconds")

    logger.info("Loading STT EN model...")
    start_time = time.time()
    en_model = WhisperModel(
        "weights/whisper_medium",
        device="cuda",
        compute_type="float16",
    )
    logger.info(f"STT EN model loaded in {time.time() - start_time:.2f} seconds")


load_model_once()
app = Flask(__name__)


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'The file was not transferred; an audio field is expected'}), 400

    request_start = time.time()
    audio_file = request.files['audio']
    ext = os.path.splitext(audio_file.filename)[1] if audio_file.filename else '.wav'
    file_path = os.path.join(AUDIO_FILES_DIR, f"{uuid.uuid4()}{ext}")
    audio_file.save(file_path)

    try:
        audio = decode_audio(file_path, sampling_rate=lid_model.feature_extractor.sampling_rate)
        audio = audio[:lid_model.feature_extractor.sampling_rate * 30]
        features = lid_model.feature_extractor(audio, padding=True)
        segment = ctranslate2.StorageView.from_array(features[None].astype(np.float32))
        results = lid_model.model.detect_language(segment)
        probs = dict(results[0])
        # uk and be languages are very similar to ru and can be confused, so we identify these languages as ru
        ru_score = max((probs.get(t, 0.0) for t in ("<|ru|>", "<|be|>", "<|uk|>")), default=0.0)
        en_score = probs.get("<|en|>", 0.0)
        detected_lang = "en" if en_score > ru_score else "ru"
        logger.info(
            f"Language probabilities: "
            f"ru={probs.get('<|ru|>', 0):.3f} "
            f"be={probs.get('<|be|>', 0):.3f} "
            f"uk={probs.get('<|uk|>', 0):.3f} "
            f"en={probs.get('<|en|>', 0):.3f} → {detected_lang}"
        )

        if detected_lang == 'en':
            segments, _ = en_model.transcribe(file_path, language="en", without_timestamps=True)
            text = "".join(segment.text for segment in segments)
        else:
            text = str(ru_model.transcribe_longform(file_path))

        logger.info(f"The request was completed in {time.time() - request_start:.2f} seconds")
        return jsonify({'text': text}), 200
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(file_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ['WEBSERVER_PORT']))