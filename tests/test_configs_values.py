import pytest

from testsuite.databases import pgsql


POSTGRES_DEFAULT_COMMAND_CONTROL = {
    'network_timeout_ms': 750,
    'statement_timeout_ms': 500,
}

POSTGRES_CONNECTION_POOL_SETTINGS = {
    '__default__': {
        'min_pool_size': 4,
        'max_pool_size': 15,
        'max_queue_size': 200,
    },
}

POSTGRES_CONNECTION_POOL_SETTINGS_2 = {
    '__default__': {
        'min_pool_size': 10,
        'max_pool_size': 30,
        'max_queue_size': 100,
    },
}

USERVER_RPS_CCONTROL_DISABLED = True

CUSTOM_CONFIG = {'config': False}

SETUP_DB_MARK = [
    pytest.mark.pgsql(
        'uservice_dynconf',
        files=['default_configs.sql', 'custom_configs.sql'],
    ),
]


@pytest.mark.parametrize(
    'ids, service, expected',
    [
        pytest.param([], '__default__', {}, id='configs empty'),
        pytest.param(
            ['POSTGRES_DEFAULT_COMMAND_CONTROL'],
            '__default__',
            {
                'POSTGRES_DEFAULT_COMMAND_CONTROL': (
                    POSTGRES_DEFAULT_COMMAND_CONTROL
                ),
            },
            marks=SETUP_DB_MARK,
            id='add default configs',
        ),
        pytest.param(
            ['POSTGRES_DEFAULT_COMMAND_CONTROL'],
            'my-custom-service',
            {
                'POSTGRES_DEFAULT_COMMAND_CONTROL': (
                    POSTGRES_DEFAULT_COMMAND_CONTROL
                ),
            },
            marks=SETUP_DB_MARK,
            id='get config for custom service from default',
        ),
        pytest.param(
            [
                'USERVER_RPS_CCONTROL_ENABLED',
                'POSTGRES_CONNECTION_POOL_SETTINGS',
            ],
            'my-custom-service',
            {
                'USERVER_RPS_CCONTROL_ENABLED': USERVER_RPS_CCONTROL_DISABLED,
                'POSTGRES_CONNECTION_POOL_SETTINGS': (
                    POSTGRES_CONNECTION_POOL_SETTINGS_2
                ),
            },
            marks=SETUP_DB_MARK,
            id='get redefinition configs from default',
        ),
        pytest.param(
            [
                'USERVER_RPS_CCONTROL_ENABLED',
                'POSTGRES_CONNECTION_POOL_SETTINGS',
                'POSTGRES_DEFAULT_COMMAND_CONTROL',
            ],
            'my-custom-service',
            {
                'USERVER_RPS_CCONTROL_ENABLED': USERVER_RPS_CCONTROL_DISABLED,
                'POSTGRES_CONNECTION_POOL_SETTINGS': (
                    POSTGRES_CONNECTION_POOL_SETTINGS_2
                ),
                'POSTGRES_DEFAULT_COMMAND_CONTROL': (
                    POSTGRES_DEFAULT_COMMAND_CONTROL
                ),
            },
            marks=SETUP_DB_MARK,
            id='redefinition and default configs merge',
        ),
        pytest.param(
            ['CUSTOM_CONFIG'],
            'my-custom-service',
            {'CUSTOM_CONFIG': CUSTOM_CONFIG},
            marks=SETUP_DB_MARK,
            id='get custom config for service',
        ),
        pytest.param(
            ['CUSTOM_CONFIG'],
            '__default__',
            {},
            marks=SETUP_DB_MARK,
            id='custom config not find for default',
        ),
        pytest.param(
            [],
            'my-custom-service',
            {
                'USERVER_RPS_CCONTROL_ENABLED': USERVER_RPS_CCONTROL_DISABLED,
                'POSTGRES_CONNECTION_POOL_SETTINGS': (
                    POSTGRES_CONNECTION_POOL_SETTINGS_2
                ),
                'CUSTOM_CONFIG': CUSTOM_CONFIG,
            },
            marks=SETUP_DB_MARK,
            id='get configs by service',
        ),
        pytest.param(
            [],
            'custom-service',
            {},
            marks=SETUP_DB_MARK,
            id='get empty configs by service',
        ),
    ],
)
async def test_configs_values(
        check_configs_state,
        ids, service, expected
):
    await check_configs_state(
        ids=ids, service=service, expected_configs=expected,
        expected_kill_switches_enabled=[], expected_kill_switches_disabled=[]
    )


@pytest.mark.pgsql(
    'uservice_dynconf',
    files=['kill_switches.sql'],
)
async def test_configs_modes(check_configs_state):
    dynamic_config_id = 'SAMPLE_DYNAMIC_CONFIG'
    enabled_kill_switch_id = 'SAMPLE_ENABLED_KILL_SWITCH'
    disabled_kill_switch_id = 'SAMPLE_DISABLED_KILL_SWITCH'
    await check_configs_state(
        ids=[
            dynamic_config_id,
            enabled_kill_switch_id,
            disabled_kill_switch_id
        ],
        service='my-custom-service',
        expected_configs={
            dynamic_config_id: 0,
            enabled_kill_switch_id: 1,
            disabled_kill_switch_id: 2
        },
        expected_kill_switches_enabled=[enabled_kill_switch_id],
        expected_kill_switches_disabled=[disabled_kill_switch_id]
    )
