# Copyright 2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from copy import deepcopy

import etcd
from pytest import mark

from models.manager.base_manager import BaseManager
from tests.conftest import dummy_ready_volume


class TestBaseManager:
    def test_default_class_vars(self):
        assert BaseManager.KEY == 'cobalt'

    def test_all_key_not_found(self, p_etcd_client_read, base_manager):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        dir, volumes = base_manager.all()

        assert dir is None
        assert volumes == []
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_all_keys_except_the_dir(self, m_etcd_dir_result, p_etcd_client_read, p_base_manager_load_from_etcd,
                                     base_manager):
        dir_mock, entry_mock = m_etcd_dir_result

        # prepare result
        p_etcd_client_read.return_value = dir_mock
        p_base_manager_load_from_etcd.return_value = [entry_mock]

        # run
        _, volumes = base_manager.all()

        # make the needed assertions
        p_base_manager_load_from_etcd.assert_called_with([entry_mock])
        assert volumes == [entry_mock]
        p_etcd_client_read.assert_called_with(BaseManager.KEY, sorted=True)

    def test_all_keys(self, mocker, base_manager, p_base_manager_all):
        key = 1
        entry = mocker.MagicMock(key=key)
        p_base_manager_all.return_value = (None, [entry])

        keys = base_manager.all_keys()

        assert p_base_manager_all.called
        assert keys == [key]

    def test_all_keys_no_result(self, base_manager, p_base_manager_all):
        p_base_manager_all.return_value = (None, [])

        keys = base_manager.all_keys()

        assert p_base_manager_all.called
        assert keys == []

    def test_by_id_key_not_found(self, base_manager, p_etcd_client_read):
        p_etcd_client_read.side_effect = etcd.EtcdKeyNotFound

        volume = base_manager.by_id('1')

        assert volume is None
        p_etcd_client_read.assert_called_with('/{}/{}'.format(base_manager.KEY, '1'))

    def test_by_id(self, p_etcd_client_read, p_base_manager_load_from_etcd, base_manager, mocker):
        etcd_result_mock = mocker.MagicMock()
        p_etcd_client_read.side_effect = etcd_result_mock
        p_base_manager_load_from_etcd.return_value = etcd_result_mock

        volume = base_manager.by_id('1')

        assert volume == etcd_result_mock
        p_etcd_client_read.assert_called_with('/{}/{}'.format(BaseManager.KEY, '1'))

    @mark.parametrize('suffix', ['', 'suffix'])
    def test_volume_create(self, suffix, p_etcd_client_write, p_base_manager_load_from_etcd, p_json_dumps,
                           base_manager, mocker):
        p_json_dumps.return_value = '{}'
        etcd_result_mock = mocker.MagicMock(name='', value='{}')
        p_etcd_client_write.return_value = etcd_result_mock
        p_base_manager_load_from_etcd.return_value = etcd_result_mock

        result = base_manager.create({}, suffix=suffix)

        append = True if suffix == '' else False
        p_json_dumps.assert_called_with({})
        p_etcd_client_write.assert_called_with('/{}/{}'.format(BaseManager.KEY, suffix),
                                               '{}',
                                               append=append)

        p_base_manager_load_from_etcd.assert_called_with(etcd_result_mock)
        assert result == etcd_result_mock

    @mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_volume_update_etcd_errors(self, p_etcd_client_update, p_json_dumps, base_manager, error):
        volume = deepcopy(dummy_ready_volume)
        p_json_dumps.return_value = {'name': 'test'}

        p_etcd_client_update.side_effect = error
        output_volume = base_manager.update(volume)

        assert not output_volume
        assert p_etcd_client_update.called

    def test_volume_update_etcd(self, p_etcd_client_update, base_manager, p_base_manager_load_from_etcd,
                                p_json_dumps):
        volume = deepcopy(dummy_ready_volume)

        p_json_dumps.return_value = {'name': 'test'}
        p_etcd_client_update.update.return_value = volume
        p_base_manager_load_from_etcd.return_value = volume

        output_volume = base_manager.update(volume)

        assert output_volume
        assert output_volume.value == volume.value

    @mark.parametrize('watch_index,watch_timeout', [
        [0, 1],
        [None, 0]
    ])
    def test_watch(self, mocker, base_manager, p_etcd_client_watch, p_base_manager_load_from_etcd, watch_index,
                   watch_timeout):
        entry = mocker.MagicMock(action='')
        p_etcd_client_watch.return_value = entry
        p_base_manager_load_from_etcd.return_value = entry

        result = base_manager.watch(index=watch_index, timeout=watch_timeout)

        p_base_manager_load_from_etcd.assert_called_with(entry)
        p_etcd_client_watch.assert_called_with(BaseManager.KEY, index=watch_index, timeout=watch_timeout,
                                               recursive=True)
        assert result == entry

    def test_watch_delete(self, mocker, base_manager, p_etcd_client_watch, p_base_manager_load_from_etcd):
        entry = mocker.MagicMock()
        type(entry).action = mocker.PropertyMock(return_value='delete')

        p_etcd_client_watch.return_value = entry

        result = base_manager.watch()

        assert not p_base_manager_load_from_etcd.called
        p_etcd_client_watch.assert_called_with(BaseManager.KEY, timeout=0, index=None, recursive=True)
        assert result == entry

    def test_watch_timeout(self, base_manager, p_etcd_client_watch):
        p_etcd_client_watch.side_effect = etcd.EtcdWatchTimedOut

        assert base_manager.watch() is None

    def test_delete(self, mocker, base_manager, p_etcd_client_delete):
        entity = mocker.MagicMock(key=1)
        p_etcd_client_delete.return_value = entity

        result = base_manager.delete(entity)

        assert result
        p_etcd_client_delete.assert_called_with(1)

    @mark.parametrize('error', [etcd.EtcdCompareFailed, etcd.EtcdKeyNotFound])
    def test_delete_etcd_errors(self, mocker, base_manager, p_etcd_client_delete, error):
        p_etcd_client_delete.side_effect = error

        entity = mocker.MagicMock(key=1)

        assert not base_manager.delete(entity)
        p_etcd_client_delete.assert_called_with(1)
