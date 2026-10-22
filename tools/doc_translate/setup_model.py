"""Download the pinned official M2M100 model and convert it for local CPU use."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'facebook/m2m100_418M'
REVISION = '55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636'
STORE = ROOT / '.translation-models'
os.environ.setdefault('HF_HOME', str(STORE / 'huggingface'))
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')

def main():
    import ctranslate2
    from huggingface_hub import snapshot_download
    from transformers import M2M100Tokenizer
    target = STORE / 'm2m100-int8'
    stamp = target / 'provenance.json'
    expected = {'model': MODEL, 'revision': REVISION, 'quantization': 'int8'}
    if stamp.exists():
        if json.loads(stamp.read_text()) != expected:
            raise RuntimeError('Existing model has different provenance; preserve it and choose another directory.')
        print('Pinned local translation model already prepared.', flush=True)
        return
    # Never overwrite a partially converted or unrelated model directory.
    if target.exists():
        raise RuntimeError(f'Inspect incomplete model directory before retrying: {target}')
    print('Downloading official model and converting to CPU int8...', flush=True)
    # Convert a local pinned snapshot. This also avoids Transformers starting
    # an unrelated background safetensors conversion request on the Hub.
    snapshot = snapshot_download(MODEL, revision=REVISION, allow_patterns=[
        'config.json', 'pytorch_model.bin', 'sentencepiece.bpe.model',
        'vocab.json', 'tokenizer_config.json', 'special_tokens_map.json', 'README.md'
    ])
    converter = ctranslate2.converters.TransformersConverter(snapshot)
    converter.convert(str(target), quantization='int8')
    tokenizer = M2M100Tokenizer.from_pretrained(snapshot, local_files_only=True)
    tokenizer.save_pretrained(str(target))
    stamp.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
    print(f'Model ready: {target}', flush=True)

if __name__ == '__main__':
    main()
