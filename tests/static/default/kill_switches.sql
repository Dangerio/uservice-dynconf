INSERT INTO uservice_dynconf.configs (service, config_name, config_value, config_mode)
VALUES 
('my-custom-service', 'SAMPLE_DYNAMIC_CONFIG', '0', 'dynamic_config'),
('my-custom-service', 'SAMPLE_ENABLED_KILL_SWITCH', '1', 'kill_switch_enabled'),
('my-custom-service', 'SAMPLE_DISABLED_KILL_SWITCH', '2', 'kill_switch_disabled');
