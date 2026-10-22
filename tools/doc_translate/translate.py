"""Local, cached English prose translation. Never feed source code or formula fields.

Input: {"strings": {"stable.key": "English prose"}}; output: same keys plus provenance.
Protected spans are copied byte-for-byte. If a model damages a placeholder, only
the intervening prose spans are translated. This fallback can reduce fluency.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from setup_model import ROOT, STORE, MODEL, REVISION

VERSION = 'protected-sentences-v2-beam4'
GUIDE = ROOT / 'docs/opencv-2.4-manuals/learning'

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def protector(terms):
    # Longer terms win. Boundaries prevent matching e.g. R inside an English word.
    literal = '|'.join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(r'https?://[^\s]+|`[^`]+`|(?<![\w])(?:' + literal +
                      r')(?![\w])|(?<![\w])\d+(?:[./]\d+)*(?![\w])')

def segments(text, pattern):
    parts, cursor = [], 0
    for match in pattern.finditer(text):
        # English article, as opposed to our named confidence variable A.
        if match.group() == 'A' and re.match(r' (?!(?:is|must|can)\b)(?:[a-z]|\d)', text[match.end():]):
            continue
        if match.start() > cursor:
            parts.append((False, text[cursor:match.start()]))
        parts.append((True, match.group()))
        cursor = match.end()
    if cursor < len(text):
        parts.append((False, text[cursor:]))
    return parts

def has_prose(text):
    return bool(re.search('[a-zA-Z]', text))

def split_sentences(text):
    # Protected decimals, identifiers and URLs have already been masked.
    # Keeping sentences separate prevents paragraph-level summarisation.
    return re.split(r'(?<=[.!?])\s+(?=[A-Za-z_])', text.strip())

class Engine:
    def __init__(self, model_dir, cache_path, threads):
        import ctranslate2
        from transformers import M2M100Tokenizer
        self.tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
        self.tokenizer.src_lang = 'en'
        self.translator = ctranslate2.Translator(str(model_dir), device='cpu', compute_type='int8', intra_threads=threads)
        self.cache_path = cache_path
        self.cache = read(cache_path) if cache_path.exists() else {}
        self.calls = 0

    def batch(self, texts, language):
        split = [split_sentences(t) for t in texts]
        unique = list(dict.fromkeys(t for sentences in split for t in sentences if has_prose(t)))
        def key(t):
            return digest([MODEL, REVISION, VERSION, language, t])
        missing = [t for t in unique if key(t) not in self.cache]
        target = self.tokenizer.get_lang_token(language)
        for start in range(0, len(missing), 16):
            batch = missing[start:start+16]
            source = [self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(t)) for t in batch]
            if any(len(tokens)>480 for tokens in source):
                raise ValueError('Split prose into shorter catalog entries (maximum 480 source tokens).')
            results = self.translator.translate_batch(source, target_prefix=[[target]]*len(source), beam_size=4, max_decoding_length=512)
            for index,(text, result) in enumerate(zip(batch, results)):
                tokens = result.hypotheses[0]
                if len(tokens)>=512:
                    print(f'  {language}: retrying a repetitive sentence with constrained decoding',flush=True)
                    retry = self.translator.translate_batch([source[index]],target_prefix=[[target]],beam_size=1,no_repeat_ngram_size=4,max_decoding_length=256)
                    tokens = retry[0].hypotheses[0]
                    if len(tokens)>=256:
                        raise RuntimeError(f'Translation hit decoding limit; split this entry: {text!r}')
                translated = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(tokens), skip_special_tokens=True).strip()
                if not translated:
                    retry = self.translator.translate_batch([source[index]], target_prefix=[[target]], beam_size=1, min_decoding_length=2, max_decoding_length=256)
                    translated = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(retry[0].hypotheses[0]), skip_special_tokens=True).strip()
                    if not translated and re.search(r'__\d+__', text):
                        # Force the protected-span fallback instead of publishing empty text.
                        translated = '__translation_failed__'
                    elif not translated:
                        raise RuntimeError(f'Empty translation; refusing incomplete output: {language}/{text!r}')
                self.cache[key(text)] = translated
            self.calls += len(batch)
            write(self.cache_path, self.cache)
            print(f'  {language}: {min(start+len(batch),len(missing))}/{len(missing)} new text segments',flush=True)
        return [' '.join(self.cache[key(t)] if has_prose(t) else t for t in sentences) for sentences in split]

def translate_catalog(strings, language, engine, pattern):
    prepared = {}
    for key, source in strings.items():
        parts = segments(source, pattern)
        protected = [text for keep,text in parts if keep]
        counter = iter(range(len(protected)))
        masked = ''.join(f'__{next(counter)}__' if keep else text for keep,text in parts)
        prepared[key] = (parts, protected, masked)
    translated = engine.batch([item[2] for item in prepared.values()], language)
    output, failed = {}, []
    for (key, (parts, protected, masked)), target in zip(prepared.items(), translated):
        expected = [f'__{i}__' for i in range(len(protected))]
        found = re.findall(r'__\d+__', target)
        if sorted(found) != sorted(expected) or '__' in re.sub(r'__\d+__','',target):
            failed.append(key)
            continue
        for token, original in zip(expected, protected):
            target = target.replace(token, original)
        output[key] = target
    # Deterministic fallback keeps exact symbols, equations and numeric values.
    fragments = [text.strip() for key in failed for keep,text in prepared[key][0] if not keep and has_prose(text)]
    replacements = dict(zip(fragments, engine.batch(fragments, language)))
    for key in failed:
        restored = []
        for keep, text in prepared[key][0]:
            if keep or not has_prose(text):
                restored.append(text)
            else:
                left = text[:len(text)-len(text.lstrip())]
                right = text[len(text.rstrip()):]
                restored.append(left + replacements[text.strip()] + right)
        output[key] = ''.join(restored)
    return {key:output[key] for key in strings}, failed

def build_bundle(guide, registry, source, glossary):
    catalogs = {}
    for lang in registry:
        item = read(guide / 'i18n' / (lang['id'] + '.json'))
        if set(item['strings']) != set(source['strings']):
            raise ValueError(f"Missing or extra keys: {lang['id']}")
        if lang['id'] not in ('sl','en') and item.get('sourceDigest') != digest([source['strings'],glossary,VERSION]):
            raise ValueError(f"Stale translation: {lang['id']}; regenerate first")
        if any(not isinstance(t,str) or not t.strip() for t in item['strings'].values()):
            raise ValueError(f"Empty translation: {lang['id']}")
        correction_path = Path(__file__).with_name('corrections') / (lang['id']+'.json')
        if correction_path.exists():
            corrections = read(correction_path)
            for key, correction in corrections['entries'].items():
                if key not in source['strings'] or correction['source'] != source['strings'][key]:
                    raise ValueError(f"Stale correction: {lang['id']}/{key}; review it against the changed source")
                if not correction['translation'].strip():
                    raise ValueError(f"Empty correction: {lang['id']}/{key}")
                item['strings'][key] = correction['translation']
            item['corrections'] = list(corrections['entries'])
            item['correctionStatus'] = corrections['status']
        catalogs[lang['id']] = item
    pattern = protector(glossary['terms'])
    protected_runs = sorted({text for source_text in source['strings'].values() for keep,text in segments(source_text,pattern) if keep},key=len,reverse=True)
    bundle = {'languages':registry,'catalogs':catalogs,'protectedRuns':protected_runs}
    (guide/'translations.js').write_text('// Generated by tools/doc_translate; contains prose only.\nwindow.TRANSLATIONS = '+json.dumps(bundle,ensure_ascii=False)+';\n',encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=GUIDE/'i18n/en.json')
    parser.add_argument('--output',type=Path,default=GUIDE/'i18n')
    parser.add_argument('--glossary',type=Path,default=Path(__file__).with_name('protected.json'))
    parser.add_argument('--languages',nargs='+',help='M2M100 codes, e.g. de ja ar; default: configured guide languages')
    parser.add_argument('--threads',type=int,default=8)
    parser.add_argument('--bundle-only',action='store_true')
    parser.add_argument('--no-bundle',action='store_true',help='Translate an independent catalog without rebuilding the guide')
    args = parser.parse_args()
    source,glossary = read(args.input),read(args.glossary)
    registry = read(Path(__file__).with_name('languages.json'))
    if not isinstance(source.get('strings'),dict) or any(not isinstance(v,str) for v in source['strings'].values()):
        raise ValueError('Input must contain a flat strings mapping of prose keys to text.')
    if not args.bundle_only:
        engine = Engine(STORE/'m2m100-int8',STORE/'translation-cache.json',args.threads)
        targets = args.languages or [lang['id'] for lang in registry if lang['id'] not in ('sl','en')]
        pattern = protector(glossary['terms'])
        for language in targets:
            if language not in engine.tokenizer.lang_code_to_id or language=='en':
                raise ValueError(f'Unsupported target language: {language}')
            if args.output.resolve()==(GUIDE/'i18n').resolve() and language=='sl':
                raise ValueError('The authored Slovenian guide must not be overwritten by machine translation.')
            print(f'Translating {language}: {len(source["strings"])} entries...',flush=True)
            strings, failed = translate_catalog(source['strings'],language,engine,pattern)
            write(args.output/(language+'.json'),{'locale':language,'status':'machine-unreviewed','model':MODEL,'revision':REVISION,'pipelineVersion':VERSION,'sourceDigest':digest([source['strings'],glossary,VERSION]),'protectedFallbackKeys':failed,'strings':strings})
            print(f'{language}: saved; protected-span fallback used for {len(failed)} entries.',flush=True)
        print(f'New inference requests: {engine.calls}',flush=True)
    if not args.no_bundle:
        build_bundle(GUIDE,registry,source,glossary)
        print('Offline translation bundle built.',flush=True)

if __name__=='__main__':
    main()
