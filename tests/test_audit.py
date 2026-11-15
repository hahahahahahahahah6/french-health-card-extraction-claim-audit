"""Regression suite: fixtures are parsed as text, never imported or executed."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from french_health_card_extraction_claim_audit.audit import audit, document_claims, module_evidence, normalize
from french_health_card_extraction_claim_audit.__main__ import main
from french_health_card_extraction_claim_audit.phrases import GENERIC_NAMES, FRENCHHEALTHCARDEXTRACTION, NOFRENCHHEALTHCARDEXTRACTION

EXPECTED_POSITIVE = ('carte vitale extraction', 'extract carte vitale', 'extracts carte vitale', 'extracting carte vitale', 'extract carte vitales', 'extracts carte vitales', 'extracting carte vitales', 'carte vitale parsing', 'carte vitale parser', 'parse carte vitale', 'parses carte vitale', 'parse carte vitales', 'parses carte vitales', 'carte vitale data extraction', 'extract carte vitale data', 'carte vitale field extraction', 'carte vitale document extraction', 'extract carte vitale documents', 'carte vitale reader', 'carte vitale scanning', 'scan carte vitale', 'scans carte vitale', 'scanning carte vitale', 'carte vitale recognition', 'recognize carte vitale', 'french health card extraction', 'extract french health cards', 'extracts french health cards', 'extracting french health cards', 'extract french health card', 'extracts french health card', 'extracting french health card', 'french health card parsing', 'french health card parser', 'parse french health cards', 'parses french health cards', 'parse french health card', 'parses french health card', 'french health card data extraction', 'extract french health card data', 'french health card field extraction', 'french health card document extraction', 'extract french health card documents', 'french health card reader', 'french health card scanning', 'scan french health card', 'scans french health card', 'scanning french health card', 'french healthcard extraction', 'extract french healthcard')
EXPECTED_NEGATIVE = ('no carte vitale extraction', 'does not extract carte vitale', 'does not extract carte vitales', 'does not support carte vitale extraction', 'without carte vitale extraction', 'no carte vitale parser', 'does not parse carte vitale', 'does not parse carte vitales', 'no french health card extraction', 'does not extract french health cards', 'does not extract french health card', 'does not support french health card extraction', 'without french health card extraction', 'no french health card parser', 'does not parse french health cards', 'does not parse french health card', 'carte vitale extraction not supported', 'french health card extraction not supported', 'no french healthcard extraction', 'does not extract french healthcard', 'does not scan carte vitale', 'does not scan french health card', 'no carte vitale reader', 'no french health card reader')
EXPECTED_GENERIC = ('extract_carte_vitale', 'extract_carte_vitales', 'parse_carte_vitale', 'parse_carte_vitales', 'extract_french_health_card', 'extract_french_health_cards', 'parse_french_health_card', 'parse_french_health_cards', 'extract_french_healthcard', 'parse_french_healthcard', 'carte_vitale_extraction', 'french_health_card_extraction', 'extract_carte_vitale_data', 'parse_carte_vitale_data', 'extract_french_health_card_data', 'parse_french_health_card_data', 'read_carte_vitale', 'read_french_health_card', 'scan_carte_vitale', 'scan_french_health_card', 'carte_vitale_reader', 'french_health_card_reader', 'get_carte_vitale_data', 'get_french_health_card_data')

PAIR = 'from mindee import Client\nc = Client()\nc.parse(HealthCardV1, source)\n'
OTHER_PRODUCTS = '''ReceiptV5 InvoiceV4 InvoiceSplitterV1 FinancialDocumentV1 PassportV1 BankCheckV1 BankAccountDetailsV1 BankAccountDetailsV2 PayslipV2 PayslipV3 NutritionFactsLabelV1 HealthcareCardV1 BusinessCardV1 CustomV1 GeneratedV1 BillOfLadingV1 ResumeV1 DeliveryNoteV1 DriverLicenseV1 IdCardV1 InternationalIdV2 CarteGriseV1 EnergyBillV1 MaterialCertificateV1 BarcodeReaderV1 CropperV1 UsMailV2 UsMailV3 MultiReceiptsDetectorV1 IdCardV2 HealthCardV2 TypeHealthCardV1'''.split()
NOT_CALLS = '''extract_receipts begin_analyze_document process_document process_document_url process_any_document process_any_document_url split_and_process_pdf split_and_process_pdf_url process_health_card process_carte_vitale process_french_health_card process_health_card_url extract_health_card parse_health_card extract_health_cards parse_health_cards extract_health_card_data parse_health_card_data process_w2_document process_w9_document process_w8_document split_and_process_w2 split_and_process_w2_url process_check process_check_url process_check_with_remittance process_check_with_remittance_url process_bank_statement_document process_bank_statement_document_url process_bussines_card_document process_bussines_card_document_url classify_document get_business_cards get_business_card delete_business_card get_pdf get_documents_from_pdf batch_process_documents analyze_document analyze_expense analyze_id start_document_analysis get_expense_analysis extract extract_text image_to_string read_csv read_excel read_pdf convert_into extract_table extract_tables find_table find_tables findContours boundingRect YOLO is_health_card detect_document detect_objects document_detector object_detector search findall parse_string upload parse load_data'''.split()


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')
        return file

    def evidence(self, code):
        return module_evidence(code, 'app.py')

    def cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                status = main(list(args))
            except SystemExit as error:
                status = error.code
        return status, stdout.getvalue(), stderr.getvalue()

    def test_exact_vocabulary(self):
        self.assertEqual(FRENCHHEALTHCARDEXTRACTION, EXPECTED_POSITIVE)
        self.assertEqual(NOFRENCHHEALTHCARDEXTRACTION, EXPECTED_NEGATIVE)
        self.assertEqual(GENERIC_NAMES, EXPECTED_GENERIC)
        self.assertEqual(tuple(map(len, (set(EXPECTED_POSITIVE), set(EXPECTED_NEGATIVE), set(EXPECTED_GENERIC)))), (50, 24, 24))

    def test_normalization(self):
        self.assertEqual(normalize("DOESN'T\n extract carte-vitale"), 'does not extract carte vitale')
        claims = document_claims("Doesn't extract carte-vitale", 'README.md')
        self.assertEqual([x['family'] for x in claims], ['NOFRENCHHEALTHCARDEXTRACTION'])

    def test_boundaries(self):
        self.assertEqual(document_claims('xcarte vitale extractionx', 'README.md'), [])

    def test_longest_and_tie(self):
        claims = document_claims('extract carte vitale documents and extract carte vitale', 'README.md')
        self.assertEqual([x['phrase'] for x in claims], ['extract carte vitale documents', 'extract carte vitale'])

    def test_paragraphs_and_inline(self):
        claims = document_claims('Heading\n\nWe `extract carte vitale`\ndata.\n\nNo carte vitale extraction', 'README.md')
        self.assertEqual([x['line'] for x in claims], [3, 6])
        self.assertEqual([x['family'] for x in claims], ['FRENCHHEALTHCARDEXTRACTION', 'NOFRENCHHEALTHCARDEXTRACTION'])

    def test_multiple_denials_removed(self):
        claims = document_claims('does not extract carte vitale; no carte vitale extraction; extract carte vitale', 'README.md')
        self.assertEqual([x['family'] for x in claims].count('FRENCHHEALTHCARDEXTRACTION'), 1)

    def test_four_space_fence_is_prose(self):
        self.assertTrue(document_claims('    ```\ncarte vitale extraction\n    ```', 'README.md'))

    def test_unclosed_fence(self):
        self.assertEqual(document_claims('~~~\ncarte vitale extraction', 'README.md'), [])

    def test_wrong_fence_cannot_close(self):
        self.assertEqual(document_claims('````\n```\ncarte vitale extraction\n~~~~\ncarte vitale extraction', 'README.md'), [])

    def test_mindee_alias(self):
        self.assertTrue(self.evidence('from mindee import Client as C\nc=C()\nc.parse(product.HealthCardV1, source)'))

    def test_mindee_direct(self):
        self.assertTrue(self.evidence('import mindee\nc=mindee.Client()\nx.parse(source, product_class=mindee.product.HealthCardV1)'))

    def test_source_fingerprint_does_not_validate_sdk_version(self):
        self.assertTrue(self.evidence('from mindee import Client\nfrom mindee.v1.product import HealthCardV1\nc=Client()\nc.parse(HealthCardV1, source)'))

    def test_mindee_alias_module_is_outside_exact_client_form(self):
        self.assertEqual(self.evidence('import mindee as m\nc=m.Client()\nc.parse(HealthCardV1, source)'), [])

    def test_split_modules(self):
        self.write('README.md', 'carte vitale extraction')
        self.write('one.py', 'from mindee import Client\nc=Client()')
        self.write('two.py', 'import mindee\nc.parse(HealthCardV1, source)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'HIGH')

    def test_import_gate(self):
        self.assertEqual(self.evidence('c=mindee.Client()\nc.parse(HealthCardV1, source)'), [])

    def test_lone_parts(self):
        for text in ('import mindee', 'from mindee import Client\nc=Client()', 'import mindee\nc.parse(HealthCardV1, x)'):
            with self.subTest(text=text):
                self.assertEqual(self.evidence(text), [])

    def test_invalid_syntax(self):
        self.assertEqual(self.evidence('x.extract_carte_vitale(\n'), [])

    def test_comments_strings_references(self):
        self.assertEqual(self.evidence('# x.extract_carte_vitale()\ns="x.extract_carte_vitale()"\nx.extract_carte_vitale'), [])

    def test_dead_code_counts(self):
        self.assertTrue(self.evidence('if False:\n    x.extract_carte_vitale()'))

    def test_subprocess(self):
        self.assertEqual(self.evidence('import subprocess\nsubprocess.run(["mindee", "extract_carte_vitale"])'), [])

    def test_eden_and_raw_http(self):
        for url in ('https://api.edenai.run/v2/universal-ai', 'https://api.veryfi.com/api/v8/partner/documents', 'https://app.nanonets.com/api/v2/OCR/Model/opaque/LabelFile/'):
            self.assertEqual(self.evidence('import requests\nrequests.post(' + repr(url) + ', json={"model":"carte_vitale"})'), [])

    def test_ocr_regex_csv_pdf_shapes(self):
        self.assertEqual(self.evidence('import re\ntext=p.extract_text()\nre.findall("NIR", text)\nboxes=[(0,0,1,1)]\nfor page in reader.pages:\n writer.add_page(page)\ncv2.findContours(image, mode, method)\npandas.read_csv(path)'), [])

    def test_positive_without_source(self):
        self.write('README.md', 'carte vitale extraction')
        result = audit(self.root)
        self.assertEqual(result['source_files'], 0)
        self.assertEqual(result['findings'][0]['rule'], 'documented-french-health-card-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')

    def test_denial_without_source(self):
        self.write('README.md', 'no carte vitale extraction')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')

    def test_denial_with_production(self):
        self.write('README.md', 'no carte vitale extraction')
        self.write('app.py', PAIR)
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['rule'], 'documented-no-french-health-card-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')

    def test_one_finding_per_family(self):
        self.write('README.md', 'carte vitale extraction\n\nextract carte vitale\n\nscan carte vitale')
        self.assertEqual(len(audit(self.root)['findings']), 1)

    def test_both_claims(self):
        self.write('README.md', 'carte vitale extraction\n\nno carte vitale extraction')
        self.write('app.py', PAIR)
        self.assertEqual([x['rule'] for x in audit(self.root)['findings']], ['documented-no-french-health-card-extraction-claim-false'])

    def test_docs_selection(self):
        self.write('other.md', 'carte vitale extraction')
        self.write('sub/README.md', 'carte vitale extraction')
        self.assertEqual(audit(self.root)['claims'], [])
        self.write('nested/docs/deep/claims.md', 'carte vitale extraction')
        self.assertEqual(len(audit(self.root)['claims']), 1)

    def test_ignore_prefix_component(self):
        self.write('README.md', 'carte vitale extraction')
        self.write('vendor/app.py', PAIR)
        self.write('vendorish/app.py', PAIR)
        self.assertEqual(len(audit(self.root, ['vendor'])['evidence']), 1)
        self.assertEqual(audit(self.root, ['vendor', 'vendorish'])['findings'][0]['severity'], 'HIGH')

    def test_symlinks(self):
        self.write('README.md', 'carte vitale extraction')
        outside = self.root / 'fixtures'
        outside.mkdir()
        self.addCleanup(lambda: __import__('shutil').rmtree(outside))
        (outside / 'app.py').write_text(PAIR)
        (self.root / 'link.py').symlink_to(outside / 'app.py')
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        self.assertEqual(audit(self.root)['evidence'], [])

    def test_cli_json_high(self):
        self.write('README.md', 'carte vitale extraction')
        code, output, _ = self.cli('audit', str(self.root), '--json')
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output)['findings'][0]['severity'], 'HIGH')

    def test_cli_test_thresholds(self):
        self.write('README.md', 'carte vitale extraction')
        self.write('tests/test_app.py', PAIR)
        self.assertEqual(self.cli('audit', str(self.root))[0], 0)
        self.assertEqual(self.cli('audit', str(self.root), '--fail-on', 'medium')[0], 2)

    def test_cli_pass_verbose_default_repo(self):
        self.write('README.md', 'carte vitale extraction')
        self.write('app.py', PAIR)
        import os
        previous = os.getcwd()
        try:
            os.chdir(self.root)
            code, output, _ = self.cli('audit', '--verbose')
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertIn('app.py:3', output)

    def test_cli_ignore_repeatable(self):
        self.write('docs/a.md', 'carte vitale extraction')
        self.write('other/docs/b.md', 'carte vitale extraction')
        self.assertEqual(self.cli('audit', str(self.root), '--ignore', 'docs', '--ignore', 'other')[0], 0)

    def test_cli_usage_errors(self):
        for args in ((), ('nope',), ('audit', '--fail-on', 'HIGH'), ('audit', '--ignore'), ('audit', '.', '--ignore', 'a', 'b'), ('audit', '--bogus')):
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args)[0], 1)

    def test_cli_bad_path(self):
        self.assertEqual(self.cli('audit', str(self.root / 'absent'))[0], 1)
        self.write('file', '')
        self.assertEqual(self.cli('audit', str(self.root / 'file'))[0], 1)

    def test_cli_io_error(self):
        with patch('french_health_card_extraction_claim_audit.__main__.audit', side_effect=PermissionError('unreadable')):
            self.assertEqual(self.cli('audit', str(self.root))[0], 1)

    def test_cli_invalid_encoding(self):
        (self.root / 'README.md').write_bytes(b'\xff')
        self.assertEqual(self.cli('audit', str(self.root))[0], 1)

    def test_cli_version(self):
        code, output, _ = self.cli('--version')
        self.assertEqual((code, output.strip()), (0, '0.1.0'))

    def test_readme_self_audit(self):
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(document_claims((repo / 'README.md').read_text(), 'README.md'), [])

    def test_no_execution(self):
        self.write('app.py', 'raise RuntimeError("must never execute")\nx.extract_carte_vitale()')
        self.assertTrue(audit(self.root)['evidence'])


def add_case(name, callback):
    callback.__name__ = 'test_' + name
    setattr(AuditTests, callback.__name__, callback)


def phrase_case(phrase, family):
    def test(self):
        claims = document_claims(phrase, 'README.md')
        self.assertEqual([(x['family'], x['phrase']) for x in claims], [(family, phrase)])
    return test


for index, phrase in enumerate(EXPECTED_POSITIVE):
    add_case('positive_phrase_%02d' % index, phrase_case(phrase, 'FRENCHHEALTHCARDEXTRACTION'))
for index, phrase in enumerate(EXPECTED_NEGATIVE):
    add_case('negative_phrase_%02d' % index, phrase_case(phrase, 'NOFRENCHHEALTHCARDEXTRACTION'))


def generic_case(name, form):
    def test(self):
        code = {'attribute': 'obj.' + name + '(image)',
                'import': 'from detector import ' + name + '\n' + name + '(image)',
                'alias': 'from detector import ' + name + ' as run\nrun(image)',
                'bare': name + '(image)',
                'import_only': 'from detector import ' + name}[form]
        self.assertEqual(bool(self.evidence(code)), form in ('attribute', 'import', 'alias'))
    return test


for name in EXPECTED_GENERIC:
    for form in ('attribute', 'import', 'alias', 'bare', 'import_only'):
        add_case('generic_' + name + '_' + form, generic_case(name, form))


def other_product_case(product):
    def test(self):
        self.assertEqual(self.evidence(PAIR.replace('HealthCardV1', product)), [])
    return test


for product in OTHER_PRODUCTS:
    add_case('not_product_' + product, other_product_case(product))


def not_call_case(name):
    def test(self):
        imports = 'import mindee, veryfi, boto3, requests, cv2, ultralytics\nimport azure.ai.documentintelligence\nimport google.cloud.documentai\n'
        self.assertEqual(self.evidence(imports + 'client.' + name + '("prebuilt-receipt")'), [])
    return test


for name in NOT_CALLS:
    add_case('not_call_' + name, not_call_case(name))


def fence_case(marker, indent):
    def test(self):
        fence = ' ' * indent + marker
        self.assertEqual(document_claims(fence + 'text\ncarte vitale extraction\n' + fence + '\n', 'README.md'), [])
    return test


for marker in ('```', '~~~~'):
    for indent in range(4):
        add_case('fence_' + str(len(marker)) + '_' + str(indent), fence_case(marker, indent))


def path_case(path, expected):
    def test(self):
        self.write('README.md', 'carte vitale extraction')
        self.write(path, PAIR)
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['severity'] if result['findings'] else 'PASS', expected)
    return test


for index, (path, expected) in enumerate((('tests/a.py', 'MEDIUM'), ('test_app.py', 'MEDIUM'), ('app_test.py', 'MEDIUM'), ('nested/tests/a.py', 'MEDIUM'), ('fixtures/a.py', 'HIGH'), ('docs/a.py', 'HIGH'), ('examples/a.py', 'HIGH'), ('nested/examples/a.py', 'HIGH'), ('app.py', 'PASS'))):
    add_case('source_path_%02d' % index, path_case(path, expected))


def shadow_case(binding, target):
    def test(self):
        code = {'generic': 'from vendor import extract_carte_vitale as run\nrun(x)',
                'client': PAIR,
                'module': 'import mindee\nc=mindee.Client()\nc.parse(HealthCardV1, x)',
                'product': PAIR}[target]
        self.assertEqual(self.evidence(code + '\n' + binding), [])
    return test


for target, name in (('generic', 'run'), ('client', 'Client'), ('module', 'mindee'), ('product', 'HealthCardV1')):
    for index, binding in enumerate(('def {n}(): pass', 'class {n}: pass', '{n} = other', '{n}: object = other', 'with other() as {n}: pass', 'async def f():\n async with other() as {n}: pass', 'class C:\n def {n}(self): pass', '({n}, other) = values')):
        add_case('shadow_' + target + '_' + str(index), shadow_case(binding.format(n=name), target))


def product_form_case(product, keyword):
    def test(self):
        code = 'import mindee\nc=mindee.Client()\nc.parse(' + ('product_class=' if keyword else '') + product + ')'
        self.assertTrue(self.evidence(code))
    return test


for index, product in enumerate(('HealthCardV1', 'product.HealthCardV1', 'mindee.product.HealthCardV1', 'mindee.product.fr.health_card.HealthCardV1')):
    for keyword in (False, True):
        add_case('product_form_' + str(index) + '_' + str(keyword), product_form_case(product, keyword))


def attribute_shadow_case(name, binding):
    def test(self):
        self.assertEqual(self.evidence('obj.' + name + '(image)\n' + binding.format(n=name)), [])
    return test


for name in EXPECTED_GENERIC:
    for index, binding in enumerate(('def {n}(): pass', 'class C:\n def {n}(self): pass', '{n} = replacement', '{n}: object = replacement', 'with manager() as {n}: pass', 'async def f():\n async with manager() as {n}: pass')):
        add_case('attribute_shadow_' + name + '_' + str(index), attribute_shadow_case(name, binding))




def excluded_source_case(source):
    def test(self):
        self.assertEqual(self.evidence(source), [])
    return test


for index, model in enumerate(('prebuilt-healthInsuranceCard.us', 'prebuilt-receipt', 'prebuilt-invoice', 'prebuilt-layout', 'prebuilt-read', 'prebuilt-idDocument', 'prebuilt-check.us', 'prebuilt-tax.us', 'prebuilt-bankStatement.us', 'prebuilt-payStub.us', 'prebuilt-businessCard', 'prebuilt-creditCard', 'prebuilt-contract', 'prebuilt-mortgage.us.1003', 'prebuilt-vaccinationCard', 'carte_vitale', 'french_health_card', 'arbitrary')):
    add_case('azure_any_model_%02d' % index, excluded_source_case('from azure.ai.documentintelligence import DocumentIntelligenceClient\nc=DocumentIntelligenceClient()\nc.begin_analyze_document(model_id=' + repr(model) + ', body=source)'))
    add_case('google_any_processor_%02d' % index, excluded_source_case('from google.cloud import documentai\nc=documentai.DocumentProcessorServiceClient()\nc.process_document(request={"name":' + repr(model) + '})'))
    add_case('eden_any_model_%02d' % index, excluded_source_case('import requests\nrequests.post("https://api.edenai.run/v2/universal-ai", json={"model":' + repr(model) + '})'))

for index, code in enumerate((
    'from llama_parse import LlamaParse\nLlamaParse().load_data(source)',
    'import requests\nrequests.post("https://app.nanonets.com/api/v2/OCR/Model/opaque/LabelFile/")',
    'import requests\nrequests.post("https://app.docsumo.com/api/v1/eevee/apikey/upload/")',
    'import mindee\nc=mindee.Client()\nc.enqueue_and_get_inference(source, model_id="carte_vitale")',
    'import mindee\nc=mindee.ClientV2()\nc.enqueue_and_get_inference(source, model_id="carte_vitale")',
    'from vendor import extract_health_card as run\nrun(source)',
    'import subprocess\nsubprocess.run(["veryfi", "process_carte_vitale", "card.jpg"])',
    'import re\ntext=pytesseract.image_to_string(image)\nresult={"social_security": re.search("NIR", text)}',
    'import mindee\nc=mindee.Client()\nc.parse("HealthCardV1", source)',
    'import mindee\nc=mindee.Client()\nc.parse(HealthCardV1(), source)',
)):
    add_case('excluded_route_%02d' % index, excluded_source_case(code))

for vendor in ('abbyy', 'rossum', 'klippa', 'parseur', 'extend'):
    add_case('opaque_' + vendor, excluded_source_case('import ' + vendor + '\n' + vendor + '.process(source, workflow_id="carte_vitale")'))

for name in ('process_document', 'process_document_url', 'process_any_document', 'process_any_document_url', 'process_health_card', 'process_carte_vitale', 'process_french_health_card', 'process_health_card_url', 'split_and_process_pdf', 'classify_document'):
    add_case('veryfi_' + name, excluded_source_case('from veryfi import Client\nc=Client()\nc.' + name + '(source)'))


def test_cli_ignore_order_and_shape(self):
    self.write('README.md', 'extract carte vitale')
    self.write('vendor/app.py', PAIR)
    for args in (('audit', '--ignore', 'vendor', str(self.root)), ('audit', str(self.root), '--ignore', 'vendor')):
        code, output, _ = self.cli(*(args + ('--json',)))
        report = json.loads(output)
        self.assertEqual(code, 2)
        self.assertEqual(set(report), {'verdict', 'findings', 'claims', 'evidence', 'source_files'})
        self.assertEqual(set(report['findings'][0]), {'rule', 'severity', 'message', 'claims'})
        self.assertEqual(set(report['claims'][0]), {'family', 'phrase', 'path', 'line'})
        self.assertEqual(report['evidence'], [])
        self.assertEqual(report['findings'][0]['rule'], 'documented-french-health-card-extraction-claim-false')

add_case('cli_ignore_order_and_shape', test_cli_ignore_order_and_shape)


def test_vocabulary_invariants(self):
    for phrase in EXPECTED_NEGATIVE:
        self.assertTrue(any(positive in phrase for positive in EXPECTED_POSITIVE))
    for phrase in EXPECTED_POSITIVE + EXPECTED_NEGATIVE:
        self.assertTrue(any(qualifier in phrase for qualifier in ('carte vitale', 'french health card', 'french healthcard')))
    self.assertEqual(audit(Path(__file__).resolve().parents[1])['verdict'], 'PASS')

add_case('vocabulary_invariants_and_self_audit', test_vocabulary_invariants)


if __name__ == '__main__':
    unittest.main()
