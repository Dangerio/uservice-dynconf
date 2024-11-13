INSERT INTO uservice_dynconf.configs (service, config_name, config_value, config_mode)
VALUES 
('my-custom-service', 'SAMPLE_DYNAMIC_CONFIG', '"dynconf_value"', 'dynamic_config'),
('my-custom-service', 'SAMPLE_ENABLED_KILL_SWITCH', '"ks_enabled_value"', 'kill_switch_enabled'),
('my-custom-service', 'SAMPLE_DISABLED_KILL_SWITCH', '"ks_disabled_value"', 'kill_switch_disabled');
