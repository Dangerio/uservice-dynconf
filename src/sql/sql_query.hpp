#pragma once

namespace uservice_dynconf::sql {

inline constexpr std::string_view kSelectSettingsForCache = R"~(
SELECT (service, config_name), config_value, config_mode, updated_at
FROM uservice_dynconf.configs
)~";

inline constexpr std::string_view kInsertConfigValue = R"~(
INSERT INTO uservice_dynconf.configs
(service, config_name, config_value, config_mode)
SELECT $1, d.key, d.value::jsonb, m.value::uservice_dynconf.mode
FROM jsonb_each_text($2) as d, jsonb_each_text($3) as m
WHERE d.key = m.key
ON CONFLICT (service, config_name)
DO UPDATE SET
config_value = EXCLUDED.config_value,
updated_at = NOW();
)~";

inline constexpr std::string_view kDeleteConfigValues = R"~(
DELETE FROM uservice_dynconf.configs
WHERE service = $1 and config_name IN (SELECT unnest($2));
)~";

} // namespace uservice_dynconf::sql
