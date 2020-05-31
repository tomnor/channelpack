from __future__ import print_function
import unittest
import sys
import os
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import numpy as np

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.pack as packmod

print('Testing pack module:', packmod)
print('Testing with', unittest)
print()


class TestIntKeyDict(unittest.TestCase):

    def setUp(self):
        self.emptydict = dict()
        self.ok_dict = dict({1: 'one', 2: 'two'})
        self.nok_dict = dict(one=1, two=2)
        self.ok_ikd = packmod.IntKeyDict(self.ok_dict)

    def test_is_dict(self):
        ikd = packmod.IntKeyDict()
        self.assertIsInstance(ikd, dict)

    def test_create_ok(self):
        self.assertEqual(self.ok_ikd[1], 'one')

    def test_create_nok(self):
        with self.assertRaises(TypeError):
            packmod.IntKeyDict(one=1, two=2)

    def test_update_ok(self):
        ikd = packmod.IntKeyDict()
        ikd.update({1: 'one', 2: 'two'})
        self.assertEqual(ikd[2], 'two')

    def test_create_nok_pargs(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.IntKeyDict(1)
        with self.assertRaises(TypeError):
            packmod.IntKeyDict(1, 2)
        with self.assertRaises(TypeError):
            packmod.IntKeyDict(1, 2, 3)
        with self.assertRaises(ValueError):
            packmod.IntKeyDict(['123', '345'])

    def test_update_nok_pargs(self):
        # should be normal dict errors
        ikd = packmod.IntKeyDict()
        with self.assertRaises(TypeError):
            ikd.update(1)
        with self.assertRaises(TypeError):
            ikd.update(1, 2)
        with self.assertRaises(TypeError):
            ikd.update(1, 2, 3)
        with self.assertRaises(ValueError):
            ikd.update(['123', '345'])

    def test_create_nok_pairs(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.IntKeyDict([(1), (2)])
        with self.assertRaises(ValueError):
            packmod.IntKeyDict([(1, 2, 3), (2, 3, 4)])

    def test_update_nok_pairs(self):
        # should be normal dict errors
        ikd = packmod.IntKeyDict()
        with self.assertRaises(TypeError):
            ikd.update([(1), (2)])
        with self.assertRaises(ValueError):
            ikd.update([(1, 2, 3), (2, 3, 4)])

    def test_create_ok_arg_nok_kwarg(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.IntKeyDict([(0, 1), (1, 2)], [(2, 3), (3, 4)])

    def test_update_ok_arg_nok_kwarg(self):
        # should be normal dict errors
        ikd = packmod.IntKeyDict()
        with self.assertRaises(TypeError):
            ikd.update([(0, 1), (1, 2)], [(2, 3), (3, 4)])

    def test_setitem_nok(self):
        ikd = packmod.IntKeyDict()
        with self.assertRaises(TypeError):
            ikd['one'] = 1

    def test_setitem_ok(self):
        ikd = packmod.IntKeyDict()
        ikd[1] = 'one'

    def test_setdefault_ok(self):
        ikd = packmod.IntKeyDict()
        ikd.setdefault(1, 'one')
        self.assertEqual(ikd[1], 'one')

    def test_setdefault_nok(self):
        ikd = packmod.IntKeyDict()
        with self.assertRaises(TypeError):
            ikd.setdefault('one', 1)

    def test_clear(self):
        self.assertFalse(self.ok_ikd.clear())
        self.assertFalse(self.ok_ikd)

    def test_fromkeys(self):
        newdict = self.ok_ikd.fromkeys((1, 2))
        self.assertEqual(set(newdict.keys()), set((1, 2)))

    def test_get(self):
        self.assertEqual(self.ok_ikd.get(2), 'two')

    def test_in(self):
        self.assertTrue(1 in self.ok_ikd)

    def test_items(self):
        for key, value in self.ok_ikd.items():
            self.assertTrue(key in self.ok_dict)
            self.assertTrue(value in self.ok_dict.values())

    def test_keys(self):
        for key in self.ok_ikd.keys():
            self.assertTrue(key in self.ok_dict)

    def test_pop(self):
        self.assertEqual(self.ok_ikd.pop(1), 'one')
        self.assertFalse(1 in self.ok_ikd)

    def test_popitem(self):
        self.assertEqual(len(self.ok_ikd.popitem()), 2)
        self.assertEqual(len(self.ok_ikd), 1)

    def test_values(self):
        self.assertTrue('one' in self.ok_ikd.values())


class TestNpDict(unittest.TestCase):

    # NpDict shall fail with
    # non-integer keys (IntKeyDict TypeError)
    # invalid dict constructors (dict behavour)
    # resulting arrays with ndim != 1 (ValueError)

    # NpDict shall
    # convert values to numpy arrays at any setting of value
    # use reference to array if possible (copy=False)
    # work as a normal dict in all other respects

    def setUp(self):
        self.ok_dict = dict({1: ('one', 'two'), 2: ('two', 'three')})
        self.npd = packmod.NpDict(self.ok_dict)

    def test_is_dict(self):
        npd = packmod.NpDict()
        self.assertIsInstance(npd, dict)

    def test_create_ok(self):
        self.assertEqual(self.npd[1][0], 'one')

    def test_create_nok(self):
        with self.assertRaises(TypeError):
            packmod.NpDict(one=1, two=2)

    def test_update_ok(self):
        npd = packmod.NpDict()
        npd.update({1: ('one', 'two'), 2: ('two', 'three')})
        self.assertEqual(npd[2][0], 'two')

    def test_create_nok_pargs(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.NpDict(1)
        with self.assertRaises(TypeError):
            packmod.NpDict(1, 2)
        with self.assertRaises(TypeError):
            packmod.NpDict(1, 2, 3)
        with self.assertRaises(ValueError):
            packmod.NpDict(['123', '345'])

    def test_update_nok_pargs(self):
        # should be normal dict errors
        npd = packmod.NpDict()
        with self.assertRaises(TypeError):
            npd.update(1)
        with self.assertRaises(TypeError):
            npd.update(1, 2)
        with self.assertRaises(TypeError):
            npd.update(1, 2, 3)
        with self.assertRaises(ValueError):
            npd.update(['123', '345'])

    def test_create_nok_pairs(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.NpDict([(1), (2)])
        with self.assertRaises(ValueError):
            packmod.NpDict([(1, 2, 3), (2, 3, 4)])

    def test_update_nok_pairs(self):
        # should be normal dict errors
        npd = packmod.NpDict()
        with self.assertRaises(TypeError):
            npd.update([(1), (2)])
        with self.assertRaises(ValueError):
            npd.update([(1, 2, 3), (2, 3, 4)])

    def test_create_ok_arg_nok_kwarg(self):
        # should be normal dict errors
        with self.assertRaises(TypeError):
            packmod.NpDict([(0, (1, 2)), (1, (1, 2))],
                           [(2, (3, 4)), (3, (3, 4))])

    def test_update_ok_arg_nok_kwarg(self):
        # should be normal dict errors
        npd = packmod.NpDict()
        with self.assertRaises(TypeError):
            npd.update([(0, 1), (1, 2)], [(2, 3), (3, 4)])

    def test_update_nok_value_pairs(self):
        npd = packmod.NpDict()
        with self.assertRaises(ValueError):
            npd.update([(1, 'one'), (2, 'two')])

    def test_setitem_nok(self):
        npd = packmod.NpDict()
        with self.assertRaises(TypeError):
            npd['one'] = 1

    def test_setitem_ok(self):
        npd = packmod.NpDict()
        npd[1] = ('one', 'two')

    def test_setdefault_ok(self):
        npd = packmod.NpDict()
        npd.setdefault(1, ('one', 'two'))
        self.assertEqual(npd[1][0], 'one')

    def test_setdefault_nok_key(self):
        npd = packmod.NpDict()
        with self.assertRaises(TypeError):
            npd.setdefault('one', (1, 2))

    def test_setdefault_nok_value(self):
        npd = packmod.NpDict()
        with self.assertRaises(ValueError):
            npd.setdefault(1, 'one')

    def test_clear(self):
        self.assertFalse(self.npd.clear())
        self.assertFalse(self.npd)

    def test_fromkeys_with_sequence_value(self):
        newdict = self.npd.fromkeys((1, 2), (3, 4))
        self.assertEqual(set(newdict.keys()), set((1, 2)))
        self.assertIsInstance(newdict, packmod.NpDict)

    def test_fromkeys_with_empty_sequence_value(self):
        newdict = self.npd.fromkeys((1, 2), ())
        self.assertEqual(set(newdict.keys()), set((1, 2)))
        self.assertIsInstance(newdict, packmod.NpDict)

    def test_get(self):
        self.assertEqual(self.npd.get(2)[0], 'two')

    def test_in(self):
        self.assertTrue(1 in self.npd)

    def test_items(self):
        for key, value in self.npd.items():
            self.assertTrue(key in self.ok_dict)
            self.assertTrue(np.all(value == self.npd[key]))

    def test_keys(self):
        for key in self.npd.keys():
            self.assertTrue(key in self.ok_dict)

    def test_pop(self):
        self.assertEqual(self.npd.pop(1)[0], 'one')
        self.assertFalse(1 in self.npd)

    def test_popitem(self):
        self.assertEqual(len(self.npd.popitem()), 2)
        self.assertEqual(len(self.npd), 1)

    def test_values(self):
        a1, a2 = self.npd.values()
        self.assertFalse(np.any(a1 == a2))  # one, two != two, three

    def test_array_is_not_copy(self):
        seq = range(3)
        npd = packmod.NpDict([(1, seq)])
        self.assertFalse(seq is npd[1])

    def test_array_is_copy(self):
        seq = np.array(range(3))
        npd = packmod.NpDict([(1, seq)])
        self.assertTrue(seq is npd[1])

    def test_ndim_nok_array_ndim0(self):
        a = np.array(3)
        with self.assertRaises(ValueError):
            packmod.NpDict([(1, a)])

    def test_ndim_nok_array_ndim2(self):
        a = np.array([range(3)])
        with self.assertRaises(ValueError):
            packmod.NpDict([(1, a)])

    def test_ndim_nok_scalar_ndim0(self):
        with self.assertRaises(ValueError):
            packmod.NpDict([(1, 3)])

    def test_ndim_nok_seq_ndim2(self):
        seq = [(1, 2, 3), (4, 5, 6)]
        with self.assertRaises(ValueError):
            packmod.NpDict([(1, seq)])

    def test_ndim_ok_array(self):
        a = np.array(range(3))
        self.assertIsInstance(packmod.NpDict([(1, a)]), packmod.NpDict)


class TestPackBasics(unittest.TestCase):

    def setUp(self):
        self.D1 = {0: ('A', 'B', 'C', 'D', 'E'), 1: range(5)}
        self.C1 = {0: 'letter', 1: 'number'}
        self.pack = packmod.ChannelPack(data=self.D1, chnames=self.C1)
        self.emptypack = packmod.ChannelPack()

    def test_startstop_parts(self):
        pack = self.pack
        pack.startstop(pack('letter') == pack('letter'), pack('letter') == 'C')
        self.assertEqual(len(pack.parts()), 2)

    def test_startstop_values(self):
        pack = packmod.ChannelPack()
        pack.data = {0: (1, 2, 3, 4, 5, 4, 3, 2, 1)}
        pack.startstop(pack(0) == 5, pack(0) == 1)
        expected = (5, 4, 3, 2)

        for val, compare in zip(pack(0, nof='filter'), expected):
            self.assertEqual(val, compare)

    def test_startstop_pack_apply_true(self):
        pack = packmod.ChannelPack()
        pack.data = {0: (1, 2, 3, 4, 5, 4, 3, 2, 1)}
        pack.mask = pack(0) < 4
        pack.startstop(pack(0) == 5, pack(0) == 1)  # result anded w mask
        expected = (3, 2)

        for val, compare in zip(pack(0, nof='filter'), expected):
            self.assertEqual(val, compare)

    def test_startstop_pack_apply_false(self):
        pack = packmod.ChannelPack()
        pack.data = {0: (1, 2, 3, 4, 5, 4, 3, 2, 1)}
        pack.startstop(pack(0) == 5, pack(0) == 1, apply=False)
        expected = (1, 2, 3, 4, 5, 4, 3, 2, 1)

        for val, compare in zip(pack(0, nof='filter'), expected):
            self.assertEqual(val, compare)

    def test_calls_by_int(self):

        pack = self.pack
        self.assertIsInstance(pack(0), np.ndarray)
        self.assertIsInstance(pack(1), np.ndarray)

    def test_calls_by_names(self):

        pack = self.pack
        self.assertIsInstance(pack('letter'), np.ndarray)
        self.assertIsInstance(pack('number'), np.ndarray)

    def test_calls_by_fallbacknames(self):

        pack = self.pack
        prefix = pack.FALLBACK_PREFIX
        self.assertIsInstance(pack(prefix + '0'), np.ndarray)
        self.assertIsInstance(pack(prefix + '1'), np.ndarray)

    def test_calls_by_int_expected_value(self):

        pack = self.pack
        for index, letter in enumerate(self.D1[0]):
            self.assertEqual(letter, pack(0)[index])
        for index, number in enumerate(self.D1[1]):
            self.assertEqual(number, pack(1)[index])

    def test_calls_by_names_expected_value(self):

        pack = self.pack
        for index, letter in enumerate(self.D1[0]):
            self.assertEqual(letter, pack('letter')[index])
        for index, number in enumerate(self.D1[1]):
            self.assertEqual(number, pack('number')[index])

    def test_calls_by_fallbacknames_expected_value(self):

        pack = self.pack
        prefix = pack.FALLBACK_PREFIX
        for index, letter in enumerate(self.D1[0]):
            self.assertEqual(letter, pack(prefix + str(0))[index])
        for index, number in enumerate(self.D1[1]):
            self.assertEqual(number, pack(prefix + str(1))[index])

    def test_calls_fallbackprefix_mod(self):

        pack = self.pack
        pack.FALLBACK_PREFIX = 'column'

        self.assertIsInstance(pack('column0'), np.ndarray)
        self.assertIsInstance(pack('column1'), np.ndarray)

    def test_calls_fallbackprefix_mod_expected_value(self):

        pack = self.pack
        pack.FALLBACK_PREFIX = 'column'

        for index, letter in enumerate(self.D1[0]):
            self.assertEqual(letter, pack('column0')[index])
        for index, number in enumerate(self.D1[1]):
            self.assertEqual(number, pack('column1')[index])

    def test_fallback_type_check(self):
        pack = self.pack
        with self.assertRaises(TypeError):
            pack.FALLBACK_PREFIX = None

    def test_set_chnames(self):

        pack = self.pack
        pack.set_chnames({0: 'codes', 1: 'grades'})
        self.assertIsInstance(pack('codes'), np.ndarray)
        self.assertIsInstance(pack('grades'), np.ndarray)

    def test_chnames_key_error(self):
        pack = self.pack
        self.assertRaises(KeyError, pack, 'nosuch0')
        self.assertRaises(KeyError, pack, 'nosuch1')

    def test_set_chnames_intkeydict(self):

        pack = self.pack
        pack.set_chnames({0: 'codes', 1: 'grades'})
        self.assertIsInstance(pack.chnames, packmod.IntKeyDict)

    def test_set_chnames_expected_value(self):

        pack = self.pack
        pack.set_chnames({0: 'codes', 1: 'grades'})

        for index, letter in enumerate(self.D1[0]):
            self.assertEqual(letter, pack('codes')[index])
        for index, number in enumerate(self.D1[1]):
            self.assertEqual(number, pack('grades')[index])

    def test_chnames_clear(self):

        pack = self.pack
        self.assertEqual(pack.chnames.clear(), None)
        self.assertFalse(pack.chnames)

    def test_chnames_assign(self):

        pack = self.pack
        pack.chnames = {0: '0 section-info (east)',
                        1: "1-capacity (pc's)"}
        self.assertEqual(pack.chnames[0], '0 section-info (east)')
        self.assertEqual(pack.chnames[1], "1-capacity (pc's)")

    def test_chnames_assign_wrong_type(self):

        pack = self.pack
        with self.assertRaises(ValueError):
            pack.chnames = 'channelpack'
        with self.assertRaises(TypeError):
            pack.chnames = 42

    def test_data_clear(self):
        pack = self.pack
        self.assertEqual(pack.data.clear(), None)
        self.assertFalse(pack.data)

    def test_set_data_npdict(self):

        pack = self.pack
        pack.set_data(self.D1)
        self.assertIsInstance(pack.data, packmod.NpDict)

    def test_data_assign(self):

        pack = self.pack
        pack.data = {0: range(2)}
        self.assertIsInstance(pack.data, packmod.NpDict)

    def test_data_assign_wrong_type(self):

        pack = self.pack
        with self.assertRaises(ValueError):
            pack.data = 'channelpack'
        with self.assertRaises(TypeError):
            pack.data = 42

    def test_set_nof(self):

        pack = self.pack
        pack.set_nof('nan')
        self.assertEqual(pack.nof, 'nan')
        pack.set_nof('filter')
        self.assertEqual(pack.nof, 'filter')
        pack.set_nof(None)
        self.assertIs(pack.nof, None)
        pack.nof = 'nan'
        self.assertEqual(pack.nof, 'nan')
        pack.nof = 'filter'
        self.assertEqual(pack.nof, 'filter')
        pack.nof = None
        self.assertIs(pack.nof, None)

    def test_nof_value_checking(self):
        pack = self.pack
        self.assertRaises(ValueError, pack.set_nof, 'invalid')
        self.assertRaises(ValueError, pack.set_nof, np.nan)
        with self.assertRaises(ValueError):
            pack.nof = 'invalid'
        with self.assertRaises(ValueError):
            pack.nof = np.nan

    def test_mask_value_checking(self):
        pack = self.pack
        with self.assertRaises(TypeError):
            pack.mask = None

    def test_mask_reset(self):
        pack = self.pack
        pack.mask = (pack('number') < 2) | (pack('number') > 2)
        self.assertFalse(np.all(pack.mask))
        pack.mask_reset()
        self.assertTrue(np.all(pack.mask))

    def test_append_pack(self):
        pack = self.pack
        self.assertEqual(pack(0).size, len(self.D1[0]))
        pack.append_pack(self.pack)
        self.assertEqual(pack(0).size, 2 * len(self.D1[0]))

    def test_append_pack_both_has_fn(self):
        pack1 = self.pack
        pack1.fn = 'file1'
        pack2 = packmod.ChannelPack(self.D1)
        pack2.fn = 'file2'
        pack1.append_pack(pack2)
        self.assertEqual(pack1.fn, 'file1')
        self.assertEqual(pack1.filenames, ['file1', 'file2'])

    def test_append_pack_none_has_fn(self):
        pack1 = self.pack
        pack2 = packmod.ChannelPack(self.D1)
        pack1.append_pack(pack2)
        self.assertFalse(pack1.fn)
        self.assertFalse(pack1.filenames)

    def test_append_pack_1_has_fn(self):
        pack1 = self.pack
        pack1.fn = 'file1'
        pack2 = packmod.ChannelPack(self.D1)
        pack1.append_pack(pack2)
        self.assertEqual(pack1.fn, 'file1')
        self.assertEqual(pack1.filenames, ['file1'])

    def test_append_pack_2_has_fn(self):
        pack1 = self.pack
        pack2 = packmod.ChannelPack(self.D1)
        pack2.fn = 'file2'
        pack1.append_pack(pack2)
        self.assertFalse(pack1.fn)
        self.assertEqual(pack1.filenames, ['file2'])

    def test_append_not_aligned(self):
        pack = self.pack
        D2 = {key + 1: value for key, value in self.D1.items()}
        pack2 = packmod.ChannelPack(D2)
        self.assertRaises(ValueError, pack.append_pack, pack2)

    def test_duration(self):
        pack = self.pack
        self.assertIsNone(pack.nof)
        pack.nof = 'filter'
        self.assertTrue(np.all(pack.mask))
        self.assertEqual(pack('number').size, 5)
        pack.mask = pack('number') > 2
        self.assertFalse(np.all(pack.mask))
        self.assertEqual(pack('number').size, 2)
        pack.duration(3)
        self.assertEqual(pack('number').size, 0)
        pack.nof = None
        self.assertEqual(pack('number').size, 5)
        self.assertFalse(np.all(pack.mask))

    def test_duration_mindur_false(self):
        pack = self.pack
        pack.mask = (pack('number') < 2) | (pack('letter') == 'D')
        self.assertEqual(len(pack.parts()), 2)
        pack.duration(1, mindur=False)
        self.assertEqual(len(pack.parts()), 1)
        for letter, should in zip_longest(pack('letter', nof='filter'), ['D']):
            self.assertEqual(letter, should)

    def test_counter(self):
        pack = self.pack
        counter = pack.counter('number')
        self.assertEqual(len(counter), len(pack('number')))  # all unique
        pack = packmod.ChannelPack({1: ('a', 'a', 'a', 'b', 'b')})
        self.assertEqual(pack.counter(1)['a'], 3)
        self.assertEqual(pack.counter(1)['b'], 2)

    def test_counter_empty_pack(self):
        pack = packmod.ChannelPack()
        self.assertRaises(TypeError, pack.counter)  # no arg
        self.assertRaises(KeyError, pack.counter, 0)  # no such key

    def test_records(self):
        pack = self.pack
        for index, record in enumerate(pack.records()):
            self.assertEqual(record.letter, pack('letter')[index])
            self.assertEqual(record.number, pack('number')[index])

    def test_records_partial_chnames(self):
        pack = self.pack
        pack.chnames = {0: 'section'}
        for record in pack.records():
            self.assertEqual(len(record), 1)

        for record, section in zip(pack.records(), self.D1[0]):
            self.assertEqual(record.section, section)

    def test_records_fallback_true(self):
        pack = self.pack
        for index, record in enumerate(pack.records(fallback=True)):
            self.assertEqual(record.ch0, pack('letter')[index])
            self.assertEqual(record.ch1, pack('number')[index])

    def test_records_empty_pack(self):
        pack = packmod.ChannelPack()
        count = 0

        for record in pack.records():
            count += 1

        self.assertEqual(count, 0)

    def test_records_empty_chnames_fallback_false(self):
        pack = self.pack
        pack.chnames = {}
        count = 0
        for record in pack.records():
            count += 1
        self.assertEqual(count, 0)

    def test_records_bad_chnames_fallback_false(self):
        pack = self.pack
        pack.chnames = {0: '0-invalid', 1: '1-invalid'}
        with self.assertRaises(ValueError):
            for record in pack.records():
                _rec = record   # NOQA

    def test_datakey(self):
        pack = self.pack
        self.assertRaises(KeyError, pack.datakey, 2)
        self.assertRaises(KeyError, pack.datakey, 'no such name')
        self.assertEqual(1, pack.datakey('number'))

    def test_name(self):
        pack = self.pack
        self.assertEqual(pack.name(1), 'number')

    def test_name_fallback(self):
        pack = self.pack
        self.assertEqual(pack.name(0, fallback=True),
                         pack.FALLBACK_PREFIX + '0')
        self.assertEqual(pack.name(1, fallback=True),
                         pack.FALLBACK_PREFIX + '1')
        pack.FALLBACK_PREFIX = 'column'
        self.assertEqual(pack.name(1, fallback=True), 'column1')

    def test_name_regex(self):
        pack = self.pack
        pack.chnames = {0: '0 section-info (east)',
                        1: "1-capacity (pc's)"}
        self.assertEqual(pack.name(0, firstwordonly=pack.id_rx), 'section')
        self.assertEqual(pack.name(1, firstwordonly=pack.id_rx), 'capacity')

    def test_name_keyerror(self):
        pack = self.pack
        self.assertRaises(KeyError, pack.name, 2)

    def test_name_valueerror(self):
        pack = self.pack
        self.assertRaises(KeyError, pack.name, 'nosuch')
        self.assertRaises(KeyError, pack.name, '')

    def test_parts_single_elements(self):

        pack = self.pack
        self.assertEqual(pack.parts(), [0])
        pack.mask = (pack('letter') == 'A') | (pack('letter') == 'C')
        self.assertEqual(pack.parts(), [0, 1])
        self.assertEqual(pack('number', part=0).shape, (1,))
        self.assertEqual(pack('number', part=1).shape, (1,))
        self.assertEqual(pack('letter', part=0).shape, (1,))
        self.assertEqual(pack('letter', part=1).shape, (1,))
        self.assertEqual(pack('number', part=1), np.array([2]))
        self.assertEqual(pack('letter', part=1), np.array(['C']))
        self.assertRaises(IndexError, pack, 'letter', part=2)

    def test_parts_range_elements(self):

        pack = self.pack
        self.assertTrue(np.all(pack('number') == np.array(range(5))))
        pack.mask = (pack('number') < 2) | (pack('number') > 2)
        self.assertEqual(pack.parts(), [0, 1])
        self.assertTrue(np.all(pack('number', part=0) == np.array([0, 1])))
        self.assertTrue(np.all(pack('number', part=1) == np.array([3, 4])))

    def test_parts_empty_pack(self):

        pack = packmod.ChannelPack()
        self.assertFalse(pack.parts())
        self.assertEqual(len(pack.parts()), 0)

    def test_set_nof_nan(self):
        pack = self.pack
        self.assertTrue(np.all(pack('number') == np.array(range(5))))
        pack.mask = (pack('letter') == 'A') | (pack('letter') == 'C')
        pack.set_nof('nan')
        self.assertEqual(pack('letter').size, 5)
        self.assertEqual(pack('letter').size, pack('number').size)
        self.assertEqual(set(pack('letter')), set(('A', 'C', None)))
        self.assertEqual(set(np.isnan(pack('number'))),
                         set(np.array((False, True, False, True, True))))
        for index in (1, 3, 4):
            self.assertTrue(np.isnan(pack('number')[index]))
        pack.set_nof(None)
        for index in range(5):
            self.assertFalse(np.isnan(pack('number')[index]))

    def test_call_nof_ignore(self):
        pack = self.pack
        pack.mask = (pack('letter') == 'A') | (pack('letter') == 'C')
        pack.set_nof('nan')
        for index, value in enumerate(self.D1[1]):
            self.assertEqual(pack('number', nof='ignore')[index], value)

    def test_slicelist(self):

        pack = self.pack
        self.assertEqual(len(pack.slicelist()), 1)
        self.assertEqual(len(pack.slicelist()), len(pack.parts()))
        pack.mask = (pack(0) == 'A') | (pack(0) == 'C')
        self.assertEqual(pack.parts(), [0, 1])
        self.assertEqual(len(pack.slicelist()), 2)
        self.assertEqual(len(pack.slicelist()), len(pack.parts()))
        self.assertTrue(pack.slicelist()[0] == slice(0, 1))
        self.assertTrue(pack.slicelist()[1] == slice(2, 3))

    def test_slicelist_empty_pack(self):
        pack = packmod.ChannelPack()
        self.assertFalse(pack.slicelist())
        self.assertEqual(len(pack.slicelist()), 0)

    def test_keyerror(self):

        pack = self.pack
        emptypack = self.emptypack
        self.assertRaises(KeyError, pack, 5)
        self.assertRaises(KeyError, pack, 'nosuch')
        self.assertRaises(KeyError, emptypack, 0)
        self.assertRaises(KeyError, emptypack, 'letter')
        self.assertRaises(KeyError, pack, 'letter0')
        self.assertRaises(KeyError, pack, -1)


class TestEmptyPack(unittest.TestCase):
    # test all methods with an empty pack
    pass
