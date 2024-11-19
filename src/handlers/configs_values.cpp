#include "configs_values.hpp"
#include "cache/configs_cache.hpp"
#include "docs/api/api.hpp"
#include "userver/formats/json/inline.hpp"
#include "userver/formats/json/value.hpp"
#include "userver/formats/json/value_builder.hpp"
#include "userver/utils/datetime.hpp"
#include <chrono>
#include <ctime>
#include <userver/logging/log.hpp>
#include <vector>

namespace uservice_dynconf::handlers::configs_values::post {

// namespace {
// struct RequestData {
//   std::vector<std::string> ids{};
//   std::optional<std::chrono::time_point<std::chrono::system_clock>>
//       update_since{};
//   std::string service{};
// };

// RequestData ParseRequest(const userver::formats::json::Value &request) {
//   RequestData result;
//   result.ids = request["ids"].As<std::vector<std::string>>({});
//   result.service = request["service"].As<std::string>({});
//   if (auto str_time = request["updated_since"].As<std::string>({});
//       !str_time.empty()) {
//     result.update_since = {userver::utils::datetime::Stringtime(
//         str_time, userver::utils::datetime::kDefaultTimezone,
//         userver::utils::datetime::kRfc3339Format)};
//   }
//   return result;
// }
// } // namespace

Handler::Handler(const userver::components::ComponentConfig &config,
                 const userver::components::ComponentContext &context)
    : HttpHandlerJsonBase(config, context),
      cache_(context.FindComponent<
             uservice_dynconf::cache::settings_cache::ConfigsCache>()) {}

userver::formats::json::Value Handler::HandleRequestJsonThrow(
    const userver::server::http::HttpRequest &,
    const userver::formats::json::Value &request_json,
    userver::server::request::RequestContext &) const {
  using TimePointTz = userver::utils::datetime::TimePointTz;
  const auto request_data = request_json.As<ConfigsValuesRequestBody>();
  const auto data = cache_.Get();

  constexpr TimePointTz kMinTime(
      std::chrono::system_clock::time_point::min());
  TimePointTz updated_at(kMinTime);

  const auto configs =
      request_data.ids.has_value()
          ? data->FindConfigs(request_data.service, request_data.ids.value())
          : data->FindConfigsByService(request_data.service);

  std::vector<std::string> kill_switches_enabled;
  std::vector<std::string> kill_switches_disabled;
  userver::formats::json::ValueBuilder configs_found;
  LOG_DEBUG() << "Before for";
  for (const auto &config : configs) {
    LOG_DEBUG() << "Config in for: " << config->key.config_name << " " << config->config_value;
    if (config && request_data.update_since.value_or(kMinTime).GetTimePoint() <=
                      config->updated_at.GetUnderlying()) {
      configs_found[config->key.config_name] = config->config_value;
      switch (config->mode) {
      case uservice_dynconf::models::Mode::kKillSwitchEnabled:
        kill_switches_enabled.push_back(config->key.config_name);
        break;
      case uservice_dynconf::models::Mode::kKillSwitchDisabled:
        kill_switches_disabled.push_back(config->key.config_name);
        break;
      case uservice_dynconf::models::Mode::kDynamicConfig:
        break;
      }
      updated_at = std::max(updated_at, TimePointTz{config->updated_at});
    }
  }

  // userver::formats::json::ValueBuilder builder;
  // builder["configs"] = result.ExtractValue();
  // if (!kill_switches_enabled.IsEmpty()) {
  //   builder["kill_switches_enabled"] = kill_switches_enabled.ExtractValue();
  // }
  // if (!kill_switches_disabled.IsEmpty()) {
  //   builder["kill_switches_disabled"] = kill_switches_disabled.ExtractValue();
  // }
  // builder["updated_at"] =
  //     updated_at == kMinTime ? userver::utils::datetime::Now() : updated_at;
  // return builder.ExtractValue();
  //     LOG_DEBUG() << "Config in if: " << config->key.config_name << " " << config->config_value;
  //     builder[config->key.config_name] = config->config_value;
  //     updated_at = std::max(updated_at, TimePointTz{config->updated_at});
  //   }

  ConfigsValuesResponseBody response;
  response.configs.extra = configs_found.ExtractValue();
  response.kill_switches_enabled = std::move(kill_switches_enabled);
  response.kill_switches_disabled = std::move(kill_switches_disabled);
  response.updated_at = updated_at == kMinTime  ? TimePointTz{userver::utils::datetime::Now()} : updated_at;
  return userver::formats::json::ValueBuilder{response}.ExtractValue();
}

} // namespace uservice_dynconf::handlers::configs_values::post
