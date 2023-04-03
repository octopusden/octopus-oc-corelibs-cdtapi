from unittest import TestCase

from oc_cdtapi import NexusAPI

from xml.etree import ElementTree

class GavToPathTestSuite(TestCase):
    def test_full_gav_converted_from_unicode (self):
        path = NexusAPI.gav_to_path(u'group.id:artifact:0.1:pkg:classifier')
        self.assertEqual('group/id/artifact/0.1/artifact-0.1-classifier.pkg', path)

    def test_full_gav_converted(self):
        path = NexusAPI.gav_to_path('group.id:artifact:0.1:pkg:classifier')
        self.assertEqual('group/id/artifact/0.1/artifact-0.1-classifier.pkg', path)

    def test_dict_gav_converted(self):
        gav = {"g": "group.id", "a": "artifact", "v": "0.1", "p": "pkg", "c": "classifier"}
        path = NexusAPI.gav_to_path(gav)
        self.assertEqual('group/id/artifact/0.1/artifact-0.1-classifier.pkg', path)

    def test_full_relaxed_conversion(self):
        path = NexusAPI.gav_to_path('group.id:artifact:0.1:pkg:classifier', relaxed=True)
        self.assertEqual('group/id/artifact/0.1/artifact-0.1-classifier.pkg', path)

    def test_converted_without_classifier(self):
        path = NexusAPI.gav_to_path('group.id:artifact:0.1:pkg')
        self.assertEqual('group/id/artifact/0.1/artifact-0.1.pkg', path)

    def test_default_packaging(self):
        path = NexusAPI.gav_to_path('group.id:artifact:0.1')
        self.assertEqual('group/id/artifact/0.1/artifact-0.1.jar', path)

    def test_no_version_relaxed(self):
        path = NexusAPI.gav_to_path('group.id:artifact', relaxed=True)
        self.assertEqual('group/id/artifact', path)

    def test_only_version_relaxed(self):
        path = NexusAPI.gav_to_path('group.id', relaxed=True)
        self.assertEqual('group/id', path)

    def test_only_artifact_relaxed(self):
        path = NexusAPI.gav_to_path({'a': 'art'}, relaxed=True)
        self.assertEqual('art', path)

    def test_gav_required_by_default(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_path({'g': 'group', 'a': 'art'})


class GavToFilenameTestSuite(TestCase):
    def test_filename_unicode (self):
        filename = NexusAPI.gav_to_filename(u'group.id:artifact:0.1:pkg:classifier')
        self.assertEqual("artifact-0.1-classifier.pkg", filename)

    def test_filename(self):
        filename = NexusAPI.gav_to_filename('group.id:artifact:0.1:pkg:classifier')
        self.assertEqual("artifact-0.1-classifier.pkg", filename)

    def test_classifier_is_optional(self):
        filename = NexusAPI.gav_to_filename('group.id:artifact:0.1:pkg')
        self.assertEqual("artifact-0.1.pkg", filename)

    def test_jar_is_default_packaging(self):
        filename = NexusAPI.gav_to_filename('group.id:artifact:0.1')
        self.assertEqual("artifact-0.1.jar", filename)

    def test_gav_required_for_filename(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename('group.id:artifact')


class GavToStrTestSuite(TestCase):

    def test_minimal_gav_written(self):
        gav_str = NexusAPI.gav_to_str({"g": "g", "a": "a", "v": "v"})
        self.assertEqual("g:a:v", gav_str)

    def test_packaged_gav_written(self):
        gav_str = NexusAPI.gav_to_str({"g": "g", "a": "a", "v": "v", "p": "p"})
        self.assertEqual("g:a:v:p", gav_str)

    def test_full_gav_written(self):
        gav_str = NexusAPI.gav_to_str({"g": "g", "a": "a", "v": "v", "p": "p", "c": "c"})
        self.assertEqual("g:a:v:p:c", gav_str)

    def test_classifier_needs_packaging(self):
        gav_str = NexusAPI.gav_to_str({"g": "g", "a": "a", "v": "v", "c": "c"})
        self.assertEqual("g:a:v", gav_str)

    def test_minimal_gav_required(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_str({"g": "g", "a": "a"})

    def test_classifier_none(self):
        gav_str = NexusAPI.gav_to_str({"g": "g", "a": "a", "v": "v", "p": "x", "c": ''})
        self.assertEqual(gav_str, "g:a:v:x")

class ParseGavTestSuite(TestCase):

    def test_full_gav_written(self):
        gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3:pkg')
        self.assertEqual(gav['a'], 'artifact.id')
        self.assertEqual(gav['g'], 'group.id')
        self.assertEqual(gav['p'], 'pkg')
        self.assertEqual(gav['v'], '0.1.2.3')
        self.assertIsNone(gav.get('c'))

    def test_empty_gav_written(self):
        with self.assertRaises(ValueError):
            gav = NexusAPI.parse_gav('')

    def test_parse_gav_no_pkg(self):
        gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3')
        self.assertEqual(gav['a'], 'artifact.id')
        self.assertEqual(gav['g'], 'group.id')
        self.assertEqual(gav['v'], '0.1.2.3')
        self.assertIsNone(gav.get('p'))
        self.assertIsNone(gav.get('c'))

    def test_parse_gav_no_v(self):
        with self.assertRaises(ValueError):
            gav = NexusAPI.parse_gav('group.id:artifact.id')

    def test_parse_gav_classifier(self):
        gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3:pkg:classifier')
        self.assertEqual(gav['a'], 'artifact.id')
        self.assertEqual(gav['c'], 'classifier')
        self.assertEqual(gav['g'], 'group.id')
        self.assertEqual(gav['p'], 'pkg')
        self.assertEqual(gav['v'], '0.1.2.3')

    def test_parse_gav_extra_member(self):
        with self.assertRaises(ValueError):
            gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3:pkg:classifier:wtf')

    def test_parse_gav_extra_member_relaxed(self):
        with self.assertRaises(ValueError):
            gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3:pkg:classifier:wtf', relaxed = True)

    def test_parse_gav_classifier_relaxed(self):
        gav = NexusAPI.parse_gav('group.id:artifact.id:0.1.2.3:pkg:classifier',relaxed = True)
        self.assertEqual(gav['a'], 'artifact.id')
        self.assertEqual(gav['c'], 'classifier')
        self.assertEqual(gav['g'], 'group.id')
        self.assertEqual(gav['p'], 'pkg')
        self.assertEqual(gav['v'], '0.1.2.3')
    
    def test_parse_gav_no_v_relaxed(self):
        gav = NexusAPI.parse_gav('group.id:artifact.id',relaxed = True)
        self.assertEqual(gav['g'], 'group.id')
        self.assertEqual(gav['a'], 'artifact.id')
        self.assertIsNone(gav.get('v'))
        self.assertIsNone(gav.get('p'))
        self.assertIsNone(gav.get('c'))
    
    def test_parse_gav_g_only_relaxed(self):
        gav = NexusAPI.parse_gav('group.id', relaxed = True)
        self.assertEqual(gav['g'], 'group.id')
        for _k in ['a', 'v', 'p', 'c']:
            self.assertNotIn(_k, list(gav.keys()))

    def test_parse_empty_gav_relaxed(self):
        self.assertEqual(NexusAPI.parse_gav('', relaxed = True), {})

    def test_parse_gav_dict_full(self):
        _dict = { 'g': 'groupId.test',
                  'a': 'artifactId-test',
                  'v': '0.0.0',
                  'p': 'pkg',
                  'c': 'classifierTest' }
        self.assertEqual(NexusAPI.parse_gav(_dict), _dict)

    def test_parse_gav_dict_short(self):
        _dict = { 'g': 'groupId.test',
                  'a': 'artifactId-test',
                  'v': '0.0.0'}
        self.assertEqual(NexusAPI.parse_gav(_dict), _dict)

    def test_parse_gav_dict_very_short(self):
        _dict = { 'g': 'groupId.test',
                  'v': '0.0.0'}
        with self.assertRaises(ValueError):
            NexusAPI.parse_gav(_dict)

    def test_parse_gav_dict_very_short(self):
        _dict = { 'g': 'groupId.test',
                  'v': '0.0.0'}
        self.assertEqual(NexusAPI.parse_gav(_dict, relaxed=True), _dict)


class GavToFileNameTestSuite(TestCase):
    def test_gav2fn_str_all(self):
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg', 
                NexusAPI.gav_to_filename('groupId:artifactId:0.1.2.3.4:pkg:classifier'))
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg', 
                NexusAPI.gav_to_filename('fake.group.id:artifactId:0.1.2.3.4:pkg:classifier'))

    def test_gav2fn_dict_all(self):
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg', 
                NexusAPI.gav_to_filename({
                    'g': 'groupId', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'}))

        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg',
                NexusAPI.gav_to_filename({
                    'g': 'fake.group.id', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'}))

    def test_gav2fn_str_no_g(self):
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg', 
                NexusAPI.gav_to_filename(':artifactId:0.1.2.3.4:pkg:classifier'))
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg',
                NexusAPI.gav_to_filename(':artifactId:0.1.2.3.4:pkg:classifier'))

    def test_gav2fn_dict_no_g(self):
        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg', 
                NexusAPI.gav_to_filename({
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'}))

        self.assertEqual('artifactId-0.1.2.3.4-classifier.pkg',
                NexusAPI.gav_to_filename({
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'}))

    def test_gav2fn_str_no_c(self):
        self.assertEqual('artifactId-0.1.2.3.4.pkg', 
                NexusAPI.gav_to_filename('groupId:artifactId:0.1.2.3.4:pkg'))
        self.assertEqual('artifactId-0.1.2.3.4.pkg', 
                NexusAPI.gav_to_filename('fake.group.id:artifactId:0.1.2.3.4:pkg'))

    def test_gav2fn_dict_no_c(self):
        self.assertEqual('artifactId-0.1.2.3.4.pkg', 
                NexusAPI.gav_to_filename({
                    'g': 'groupId', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg'}))

        self.assertEqual('artifactId-0.1.2.3.4.pkg',
                NexusAPI.gav_to_filename({
                    'g': 'fake.group.id', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'p': 'pkg'}))

    def test_gav2fn_str_no_v(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename('groupId:artifactId')
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename('fake.group.id:artifactId')

    def test_gav2fn_dict_no_v(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename({
                    'g': 'groupId', 
                    'a': 'artifactId',
                    'p': 'pkg',
                    'c': 'classifier'})
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename({
                    'g': 'fake.group.id', 
                    'a': 'artifactId',
                    'p': 'pkg',
                    'c': 'classifier'})

    def test_gav2fn_str_no_a(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename('groupId')
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename('fake.group.id')

    def test_gav2fn_dict_no_a(self):
        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename({
                    'g': 'groupId', 
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'})

        with self.assertRaises(ValueError):
            NexusAPI.gav_to_filename({
                    'g': 'fake.group.id', 
                    'v': '0.1.2.3.4',
                    'p': 'pkg',
                    'c': 'classifier'})

    def test_gav2fn_str_no_p(self):
        self.assertEqual('artifactId-0.1.2.3.4.jar', 
                NexusAPI.gav_to_filename('groupId:artifactId:0.1.2.3.4'))
        self.assertEqual('artifactId-0.1.2.3.4.jar', 
                NexusAPI.gav_to_filename('fake.group.id:artifactId:0.1.2.3.4'))

    def test_gav2fn_dict_no_p(self):
        self.assertEqual('artifactId-0.1.2.3.4-classifier.jar', 
                NexusAPI.gav_to_filename({
                    'g': 'groupId', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'c': 'classifier'}))

        self.assertEqual('artifactId-0.1.2.3.4-classifier.jar',
                NexusAPI.gav_to_filename({
                    'g': 'fake.group.id', 
                    'a': 'artifactId',
                    'v': '0.1.2.3.4',
                    'c': 'classifier'}))

class PomFromGavTestSuite(TestCase):
    def _parse_and_general_asserts(self, xmlstr, groupId, artifactId, version, packaging=None):
        xmlr = ElementTree.fromstring(xmlstr)
        # assert root tag
        # today we have 4.0.0 model version with a corresponding XML namespace
        _xmlns = '{http://maven.apache.org/POM/4.0.0}'
        self.assertEqual(_xmlns + 'project', xmlr.tag)
        self.assertEqual(xmlr.find(_xmlns + 'modelVersion').text, '4.0.0')

        # assert GAV - as dictionary
        self.assertEqual(xmlr.find(_xmlns + 'groupId').text, groupId)
        self.assertEqual(xmlr.find(_xmlns + 'artifactId').text, artifactId)
        self.assertEqual(xmlr.find(_xmlns + 'version').text, version)

        if packaging:
            self.assertEqual(xmlr.find(_xmlns + 'packaging').text, packaging)
        else:
            self.assertIsNone(xmlr.find(_xmlns + 'packaging'))

        return xmlr

    def test_pomFromGav_all_str(self):
        _pom = NexusAPI.pom_from_gav('groupId.1.template:artifactId-1:version-1:packaging-1:classifier-1', no_packaging=False)
        self._parse_and_general_asserts(_pom, 'groupId.1.template', 'artifactId-1', 'version-1', 'packaging-1')

    def test_pomFromGav_nopkg_str(self):
        _pom = NexusAPI.pom_from_gav('groupId.2.template:artifactId-2:version-2:packaging-2:classifier-2', no_packaging=True)
        self._parse_and_general_asserts(_pom, 'groupId.2.template', 'artifactId-2', 'version-2')

    def test_pomFromGav_short_str(self):
        _pom = NexusAPI.pom_from_gav('groupId.3.template:artifactId-3:version-3', no_packaging=False)
        self._parse_and_general_asserts(_pom, 'groupId.3.template', 'artifactId-3', 'version-3')

    def test_pomFromGav_all_dict(self):
        _test_num = 1
        _gav_d = {
                'g': 'test.group.id.%d' % _test_num,
                'a': 'artifact-id-%d' % _test_num,
                'v': '%d.%d.%d' % (_test_num, _test_num + _test_num, _test_num * _test_num),
                'p': 'pkg%d' % _test_num,
                'c': 'class-if-eyer-%d' % _test_num }

        _pom = NexusAPI.pom_from_gav(_gav_d, no_packaging=False)
        self._parse_and_general_asserts(_pom, _gav_d['g'], _gav_d['a'], _gav_d['v'], _gav_d['p'])

    def test_pomFromGav_nopkg_dict(self):
        _test_num = 2
        _gav_d = {
                'g': 'test.group.id.%d' % _test_num,
                'a': 'artifact-id-%d' % _test_num,
                'v': '%d.%d.%d' % (_test_num, _test_num + _test_num, _test_num * _test_num),
                'p': 'pkg%d' % _test_num,
                'c': 'class-if-eyer-%d' % _test_num }

        _pom = NexusAPI.pom_from_gav(_gav_d, no_packaging=True)
        self._parse_and_general_asserts(_pom, _gav_d['g'], _gav_d['a'], _gav_d['v'])

    def test_pomFromGav_short_dict(self):
        _test_num = 2
        _gav_d = {
                'g': 'test.group.id.%d' % _test_num,
                'a': 'artifact-id-%d' % _test_num,
                'v': '%d.%d.%d' % (_test_num, _test_num + _test_num, _test_num * _test_num)}

        _pom = NexusAPI.pom_from_gav(_gav_d, no_packaging=False)
        self._parse_and_general_asserts(_pom, _gav_d['g'], _gav_d['a'], _gav_d['v'])

class GavFromPathTestSuite(TestCase):
    def test_gav_string_generated_full(self):
        gav = NexusAPI.gav_from_path('/group/id/artifact/0.1/artifact-0.1-classifier.pkg', dictionary=False)
        self.assertEqual('group.id:artifact:0.1:pkg:classifier', gav)

    def test_gav_string_generated_no_classifier(self):
        gav = NexusAPI.gav_from_path('/group/id/artifact/0.1/artifact-0.1.pkg', dictionary=False)
        self.assertEqual('group.id:artifact:0.1:pkg', gav)

    def test_gav_dict_generated_full(self):
        gav = NexusAPI.gav_from_path('/group/id/artifact/0.1/artifact-0.1-classifier.pkg')
        self.assertDictEqual({'g': 'group.id', 'a': 'artifact', 'v': '0.1', 'p': 'pkg', 'c': 'classifier'}, gav)

    def test_gav_dict_generated_no_classifier(self):
        gav = NexusAPI.gav_from_path('/group/id/artifact/0.1/artifact-0.1.pkg')
        self.assertDictEqual({'g': 'group.id', 'a': 'artifact', 'v': '0.1', 'p': 'pkg'}, gav)

    def test_gav_dict_no_packaging(self):
        gav = NexusAPI.gav_from_path('group/test/help/id/factart/1.2.3.4.5.6/factart-1.2.3.4.5.6', dictionary=True)
        self.assertDictEqual(gav, {'g': 'group.test.help.id', 'a': 'factart', 'v': '1.2.3.4.5.6'})

    def test_gav_str_no_packaging(self):
        gav = NexusAPI.gav_from_path('group/test/help/id/factart/1.2.3.4.5.6/factart-1.2.3.4.5.6', dictionary=False)
        self.assertEqual(gav, 'group.test.help.id:factart:1.2.3.4.5.6')

