import pytest

from testsuite.databases import pgsql


@pytest.mark.parametrize(
    'ids, configs, kill_switches_enabled, kill_switches_disabled',
    [
        pytest.param(
            ['CUSTOM_CONFIG'],
            {'CUSTOM_CONFIG': {'config': 'value'}},
            [],
            [],
            id='add one config',
        ),
        pytest.param(
            ['CUSTOM_CONFIG', 'ADD_CONFIG', 'MORE_CONFIGS'],
            {
                'CUSTOM_CONFIG': {'config': 'value'},
                'ADD_CONFIG': 5000,
                'MORE_CONFIGS': {
                    'all': {},
                    'we': {'state': False},
                    'data': 'nor,',
                },
            },
            [],
            [],
            id='add bulk configs',
        ),
        pytest.param(
            ['ENABLED_KILL_SWITCH'],
            {'ENABLED_KILL_SWITCH': {'config': 'value'}},
            ['ENABLED_KILL_SWITCH'],
            [],
            id='add one enabled kill switch',
        ),
        pytest.param(
            ['DISABLED_KILL_SWITCH'],
            {'DISABLED_KILL_SWITCH': {'config': 'value'}},
            [],
            ['DISABLED_KILL_SWITCH'],
            id='add one disabled kill switch',
        ),
        pytest.param(
            ['DYNAMIC_CONFIG', 'ENABLED_KILL_SWITCH', 'DISABLED_KILL_SWITCH'],
            {
                'DYNAMIC_CONFIG': 1,
                'ENABLED_KILL_SWITCH': 2,
                'DISABLED_KILL_SWITCH': 3,
            },
            ['ENABLED_KILL_SWITCH'],
            ['DISABLED_KILL_SWITCH'],
            id='add bulk configs with different modes',
        ),
    ],
)
async def test_configs_add_values(
        service_client, ids, configs,
        kill_switches_enabled, kill_switches_disabled,
):
    service = 'my-service'
    response = await service_client.post(
        '/configs/values', json={'ids': ids, 'service': service},
    )
    assert response.status_code == 200
    json = response.json()
    assert json['configs'] == {}
    assert 'kill_switches_enabled' not in json
    assert 'kill_switches_disabled' not in json

    response = await service_client.post(
        '/admin/v1/configs', json={
            'service': service,
            'configs': configs,
            'kill_switches_enabled': kill_switches_enabled,
            'kill_switches_disabled': kill_switches_disabled,
        },
    )

    assert response.status_code == 204

    await service_client.invalidate_caches()
    response = await service_client.post(
        '/configs/values', json={'ids': ids, 'service': service},
    )
    assert response.status_code == 200
    json = response.json()
    assert json['configs'] == configs
    assert json.get('kill_switches_enabled', []) == kill_switches_enabled
    assert json.get('kill_switches_disabled', []) == kill_switches_disabled


@pytest.mark.pgsql(
    'uservice_dynconf',
    files=['default_configs.sql', 'custom_configs.sql'],
)
async def test_redefinitions_configs(
        service_client,
):
    ids = ['CUSTOM_CONFIG', 'MORE_CONFIGS']
    service = 'my-custom-service'
    response = await service_client.post(
        '/configs/values', json={'ids': ids, 'service': service},
    )
    assert response.status_code == 200
    assert response.json()['configs'] == {'CUSTOM_CONFIG': {'config': False}}

    configs = {
        'CUSTOM_CONFIG': {'config': True, 'data': {}, 'status': 99},
        'MORE_CONFIGS': {'__state__': 'norm', 'enabled': True, 'data': 22.22},
    }
    response = await service_client.post(
        '/admin/v1/configs', json={'service': service, 'configs': configs},
    )

    assert response.status_code == 204

    await service_client.invalidate_caches()
    response = await service_client.post(
        '/configs/values', json={'ids': ids, 'service': service},
    )
    assert response.status_code == 200
    assert response.json()['configs'] == configs


@pytest.mark.parametrize(
    'request_data',
    [
        ({}),
        ({'configs': {}}),
        ({'configs': {'CONFIG': 1000}}),
        ({'service': ''}),
        ({'service': 'my-service'}),
        ({'configs': {'CONFIG': 1000}, 'service': ''}),
        ({'configs': {}, 'service': 'my-service'}),
    ],
)
async def test_missing_required_fields(
        service_client, request_data,
):
    response = await service_client.post(
        '/admin/v1/configs', json=request_data,
    )
    assert response.status_code == 400
    assert response.json() == {
        'code': '400',
        'message': 'Fields \'configs\' and \'service\' are required',
    }


@pytest.mark.parametrize(
    'kill_switches_enabled, kill_switches_disabled',
    [
        (['FIRST_CONFIG'], ['FIRST_CONFIG']),
        (['FIRST_CONFIG'], ['FIRST_CONFIG', 'SECOND_CONFIG']),
        (['FIRST_CONFIG', 'SECOND_CONFIG'], ['FIRST_CONFIG'],),
        (['FIRST_CONFIG', 'SECOND_CONFIG'], ['SECOND_CONFIG', 'THIRD_CONFIG']),
    ],
)
async def test_overlapping_kill_switches(
        service_client, kill_switches_enabled, kill_switches_disabled,
):
    response = await service_client.post(
        '/admin/v1/configs', json={
            'configs': {
                config_id: {'config': 'value'}
                for config_id in kill_switches_enabled + kill_switches_disabled
            },
            'service': 'my-service',
            'kill_switches_enabled': kill_switches_enabled,
            'kill_switches_disabled': kill_switches_disabled,
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        'code': '400',
        'message':
            'Ids in \'kill_switches_enabled\' and \'kill_switches_disabled\' '
            'must not overlap',
    }


@pytest.mark.parametrize(
    'kill_switches_enabled, kill_switches_disabled',
    [
        (['ENABLED_KILL_SWITCH'], []),
        ([], ['DISABLED_KILL_SWITCH']),
        (['ENABLED_KILL_SWITCH'], ['DISABLED_KILL_SWITCH']),
    ],
)
async def test_kill_switches_not_from_configs(
        service_client, kill_switches_enabled, kill_switches_disabled,
):
    response = await service_client.post(
        '/admin/v1/configs', json={
            'configs': {'DYNAMIC_CONFIG': {'config': 'value'}},
            'service': 'my-service',
            'kill_switches_enabled': kill_switches_enabled,
            'kill_switches_disabled': kill_switches_disabled,
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        'code': '400',
        'message':
            'Fields \'kill_switches_enabled\' and \'kill_switches_disabled\' '
            'must consist of ids from \'configs\' field',
    }
