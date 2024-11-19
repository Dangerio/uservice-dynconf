DROP SCHEMA IF EXISTS uservice_dynconf CASCADE;

CREATE SCHEMA IF NOT EXISTS uservice_dynconf;

CREATE TYPE uservice_dynconf.mode AS ENUM ('dynamic_config', 'kill_switch_enabled', 'kill_switch_disabled');
CREATE TABLE IF NOT EXISTS uservice_dynconf.configs (
    service TEXT NOT NULL DEFAULT '__default__',
    config_name TEXT NOT NULL,
    config_value JSONB,
    config_mode uservice_dynconf.mode DEFAULT 'dynamic_config',
    created_at timestamptz DEFAULT NOW(),
    updated_at timestamptz DEFAULT NOW(),

    PRIMARY KEY (service, config_name)
);

CREATE INDEX IF NOT EXISTS idx__created_at__configs
ON uservice_dynconf.configs USING btree (created_at);

CREATE INDEX IF NOT EXISTS idx__updated_at__configs
ON uservice_dynconf.configs USING btree (updated_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx__pair_service_and_connfig
ON uservice_dynconf.configs USING btree (service, config_name);
