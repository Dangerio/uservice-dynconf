import pathlib
import typing

import pytest

from testsuite.databases.pgsql import discover

pytest_plugins = ['pytest_userver.plugins.postgresql']


@pytest.fixture(scope='session')
def service_source_dir():
    return pathlib.Path(__file__).parent.parent


@pytest.fixture(scope='session')
def initial_data_path(
        service_source_dir,
) -> typing.List[pathlib.Path]:
    """Path for find files with data"""
    return [
        service_source_dir / 'postgresql/data',
        service_source_dir,
    ]


@pytest.fixture(scope='session')
def pgsql_local(service_source_dir, pgsql_local_create):
    """Create schemas databases for tests"""
    databases = discover.find_schemas(
        'testdb',
        [service_source_dir.joinpath('postgresql/schemas')],
    )
    return pgsql_local_create(list(databases.values()))


@pytest.fixture
async def check_configs_state(service_client):
    async def check(
            ids: list[str], service: str, expected_configs: dict,
            expected_kill_switches_enabled: list[str],
            expected_kill_switches_disabled: list[str],
    ) -> bool:
        response = await service_client.post(
            '/configs/values', json={'ids': ids, 'service': service},
        )
        assert response.status_code == 200
        json = response.json()
        assert json['configs'] == expected_configs
        assert json.get('kill_switches_enabled', []
                        ) == expected_kill_switches_enabled
        assert json.get('kill_switches_disabled', []
                        ) == expected_kill_switches_disabled

    return check


@pytest.fixture
def kill_switches_configs():
    return {
        'SAMPLE_DYNAMIC_CONFIG': 0,
        'SAMPLE_ENABLED_KILL_SWITCH': 1,
        'SAMPLE_DISABLED_KILL_SWITCH': 2,
    }
