INSERT INTO uservice_dynconf.configs (service, config_name, config_value, config_mode)
VALUES 
('service-with-kill-switches', 'SAMPLE_DYNAMIC_CONFIG', '0', 'dynamic_config'),
('service-with-kill-switches', 'SAMPLE_ENABLED_KILL_SWITCH', '1', 'kill_switch_enabled'),
('service-with-kill-switches', 'SAMPLE_DISABLED_KILL_SWITCH', '2', 'kill_switch_disabled');
