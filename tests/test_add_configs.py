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
            {'ENABLED_KILL_SWITCH': 1},
            ['ENABLED_KILL_SWITCH'],
            [],
            id='add one enabled kill switch',
        ),
        pytest.param(
            ['DISABLED_KILL_SWITCH'],
            {'DISABLED_KILL_SWITCH': 2},
            [],
            ['DISABLED_KILL_SWITCH'],
            id='add one disabled kill switch',
        ),
        pytest.param(
            ['DYNAMIC_CONFIG', 'ENABLED_KILL_SWITCH', 'DISABLED_KILL_SWITCH'],
            {
                'DYNAMIC_CONFIG': 0,
                'ENABLED_KILL_SWITCH': 1,
                'DISABLED_KILL_SWITCH': 2,
            },
            ['ENABLED_KILL_SWITCH'],
            ['DISABLED_KILL_SWITCH'],
            id='add bulk configs with different modes',
        ),
    ],
)
async def test_configs_add_values(
        service_client, check_configs_state,
        ids, configs, kill_switches_enabled, kill_switches_disabled,
):
    service = 'my-service'
    await check_configs_state(
        ids=ids,
        service=service,
        expected_configs={},
        expected_kill_switches_enabled=[],
        expected_kill_switches_disabled=[],
    )

    response = await service_client.post(
        '/admin/v1/configs', json={
            'service': service,
            'configs': configs,
            'kill_switches_enabled': kill_switches_enabled,
            'kill_switches_disabled': kill_switches_disabled,
        },
    )

    assert response.status_code == 204

    await service_client.invalidate_caches(cache_names=['configs-cache'])
    await check_configs_state(
        ids=ids,
        service=service,
        expected_configs=configs,
        expected_kill_switches_enabled=kill_switches_enabled,
        expected_kill_switches_disabled=kill_switches_disabled,
    )


@pytest.mark.pgsql(
    'uservice_dynconf',
    files=['default_configs.sql', 'custom_configs.sql'],
)
async def test_redefinitions_configs(
        service_client, check_configs_state,
):
    ids = ['CUSTOM_CONFIG', 'MORE_CONFIGS']
    service = 'my-custom-service'
    await check_configs_state(
        ids=ids,
        service=service,
        expected_configs={'CUSTOM_CONFIG': {'config': False}},
        expected_kill_switches_enabled=[],
        expected_kill_switches_disabled=[],
    )

    configs = {
        'CUSTOM_CONFIG': {'config': True, 'data': {}, 'status': 99},
        'MORE_CONFIGS': {'__state__': 'norm', 'enabled': True, 'data': 22.22},
    }
    response = await service_client.post(
        '/admin/v1/configs', json={'service': service, 'configs': configs},
    )

    assert response.status_code == 204

    await service_client.invalidate_caches(cache_names=['configs-cache'])
    await check_configs_state(
        ids=ids,
        service=service,
        expected_configs=configs,
        expected_kill_switches_enabled=[],
        expected_kill_switches_disabled=[],
    )


@pytest.mark.parametrize(
    'kill_switches_enabled, kill_switches_disabled',
    [
        pytest.param(
            ['SAMPLE_DYNAMIC_CONFIG'],
            ['SAMPLE_ENABLED_KILL_SWITCH'],
            id='change config mode so that: '
               'dynconf -> ks_en; ks_en -> ks_dis; ks_dis -> dynconf',
        ),
        pytest.param(
            ['SAMPLE_DISABLED_KILL_SWITCH'],
            ['SAMPLE_DYNAMIC_CONFIG'],
            id='change config mode so that: '
               'dynconf -> ks_dis; ks_en -> dynconf; ks_dis -> ks_en',
        ),
    ],
)
@pytest.mark.pgsql(
    'uservice_dynconf',
    files=['kill_switches.sql'],
)
async def test_redefinitions_of_config_modes(
        service_client, check_configs_state,
        kill_switches_enabled, kill_switches_disabled,
):
    service = 'service-with-kill-switches'
    configs = {
        'SAMPLE_DYNAMIC_CONFIG': 0,
        'SAMPLE_ENABLED_KILL_SWITCH': 1,
        'SAMPLE_DISABLED_KILL_SWITCH': 2,
    }
    response = await service_client.post(
        '/admin/v1/configs', json={
            'service': service,
            'configs': configs,
            'kill_switches_enabled': kill_switches_enabled,
            'kill_switches_disabled': kill_switches_disabled,
        },
    )

    assert response.status_code == 204

    await service_client.invalidate_caches(cache_names=['configs-cache'])
    await check_configs_state(
        ids=list(configs.keys()),
        service=service,
        expected_configs=configs,
        expected_kill_switches_enabled=kill_switches_enabled,
        expected_kill_switches_disabled=kill_switches_disabled,
    )


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
async def test_add_configs_400(
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
        (['FIRST_CONFIG', 'SECOND_CONFIG'], ['FIRST_CONFIG']),
        (['FIRST_CONFIG', 'SECOND_CONFIG'], ['SECOND_CONFIG', 'THIRD_CONFIG']),
    ],
)
async def test_overlapping_kill_switches(
        service_client, kill_switches_enabled, kill_switches_disabled,
):
    response = await service_client.post(
        '/admin/v1/configs', json={
            'configs': {
                config_id: 0
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
            'configs': {'DYNAMIC_CONFIG': 0},
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
