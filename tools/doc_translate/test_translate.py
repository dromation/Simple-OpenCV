"""Tests for mathematical integrity and publishing guards, no model download."""
import json
import tempfile
import unittest
from pathlib import Path
from translate import segments, protector, translate_catalog, build_bundle, digest, VERSION, split_sentences

class FakeEngine:
    def __init__(self, damaged=False):
        self.damaged=damaged
    def batch(self, texts, language):
        result=[]
        for text in texts:
            target=text.replace('Previous','Prej').replace('current','zdaj')
            if self.damaged:
                target=target.replace('__0__','missing placeholder')
            result.append(target)
        return result

class IntegrityTests(unittest.TestCase):
    def test_sentence_split_keeps_all_sentences(self):
        self.assertEqual(split_sentences('Subtract the images. Preserve the sign. Inspect the result.'),['Subtract the images.','Preserve the sign.','Inspect the result.'])
        self.assertEqual(split_sentences('Use 0.5 as the value.'),['Use 0.5 as the value.'])
    def test_math_is_exact_with_valid_placeholders(self):
        source={'example':'Previous R = 0.8; current R = 0.2.'}
        result,fallback=translate_catalog(source,'sl',FakeEngine(),protector(['R = 0.8','R = 0.2']))
        self.assertEqual(result['example'],'Prej R = 0.8; zdaj R = 0.2.')
        self.assertEqual(fallback,[])

    def test_damaged_placeholder_falls_back_without_losing_math(self):
        source={'example':'Previous R = 0.8; current R = 0.2.'}
        result,fallback=translate_catalog(source,'sl',FakeEngine(True),protector(['R = 0.8','R = 0.2']))
        self.assertEqual(result['example'],'Prej R = 0.8; zdaj R = 0.2.')
        self.assertEqual(fallback,['example'])

    def test_terms_do_not_match_inside_words(self):
        parts=segments('S is signed; A threshold. A is a weight.',protector(['S','A']))
        self.assertEqual([text for keep,text in parts if keep],['S','A'])

    def test_bundle_rejects_stale_and_missing_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            guide=Path(temp); (guide/'i18n').mkdir()
            source={'strings':{'ui.title':'Title'}};glossary={'terms':['RGB']}
            catalog={'locale':'de','strings':{'ui.title':'Titel'},'sourceDigest':'stale'}
            target=guide/'i18n/de.json'
            target.write_text(json.dumps(catalog))
            with self.assertRaisesRegex(ValueError,'Stale'):
                build_bundle(guide,[{'id':'de'}],source,glossary)
            catalog['sourceDigest']=digest([source['strings'],glossary,VERSION]); catalog['strings']={}
            target.write_text(json.dumps(catalog))
            with self.assertRaisesRegex(ValueError,'Missing'):
                build_bundle(guide,[{'id':'de'}],source,glossary)
            self.assertFalse((guide/'translations.js').exists())

if __name__=='__main__':
    unittest.main()
