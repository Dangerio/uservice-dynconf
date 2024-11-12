#include "admin_v1_configs.hpp"
#include "userver/formats/json/inline.hpp"
#include "userver/formats/json/value.hpp"
#include "userver/formats/yaml/value_builder.hpp"
#include "userver/storages/postgres/cluster.hpp"
#include "userver/storages/postgres/component.hpp"

#include "models/config.hpp"
#include "sql/sql_query.hpp"
#include "utils/make_error.hpp"
#include <string>
#include <unordered_set>
#include <vector>

namespace uservice_dynconf::handlers::admin_v1_configs::post {

namespace {
struct RequestData {
  userver::formats::json::Value configs;
  std::unordered_set<std::string> kill_switches_enabled;
  std::unordered_set<std::string> kill_switches_disabled;
  std::string service{};
};

RequestData ParseRequest(const userver::formats::json::Value &request) {
  RequestData result;
  if (request["configs"].IsObject()) {
    result.configs = request["configs"];
  }
  result.service = request["service"].As<std::string>({});
  result.kill_switches_enabled =
      request["kill_switches_enabled"].As<std::unordered_set<std::string>>({});
  result.kill_switches_disabled =
      request["kill_switches_disabled"].As<std::unordered_set<std::string>>({});
  return result;
}

bool ConsitstsOfIdsFromConfigs(
    const std::unordered_set<std::string> &kill_switches,
    const userver::formats::json::Value &configs) {
  for (const auto &kill_switch : kill_switches) {
    if (!configs.HasMember(kill_switch)) {
      return false;
    }
  }
  return true;
}

bool HasIntersection(const std::unordered_set<std::string> &first,
                     const std::unordered_set<std::string> &second) {
  for (const auto &key : first) {
    if (second.count(key) > 0) {
      return true;
    }
  }
  return false;
}

userver::formats::json::Value MakeConfigModeMap(
    const userver::formats::json::Value &configs,
    const std::unordered_set<std::string> &kill_switches_enabled,
    const std::unordered_set<std::string> &kill_switches_disabled) {
  using Mode = uservice_dynconf::models::Mode;

  userver::formats::json::ValueBuilder builder;
  for (const auto &[config_name, config_value] : Items(configs)) {
    if (kill_switches_enabled.count(config_name) > 0) {
      builder[config_name] =
          uservice_dynconf::models::ToString(Mode::kKillSwitchEnabled);
    } else if (kill_switches_disabled.count(config_name) > 0) {
      builder[config_name] =
          uservice_dynconf::models::ToString(Mode::kKillSwitchDisabled);
      ;
    } else {
      builder[config_name] =
          uservice_dynconf::models::ToString(Mode::kDynamicConfig);
      ;
    }
  }

  return builder.ExtractValue();
}

} // namespace

Handler::Handler(const userver::components::ComponentConfig &config,
                 const userver::components::ComponentContext &context)
    : HttpHandlerJsonBase(config, context),
      cluster_(
          context
              .FindComponent<userver::components::Postgres>("settings-database")
              .GetCluster()) {}

userver::formats::json::Value Handler::HandleRequestJsonThrow(
    const userver::server::http::HttpRequest &request,
    const userver::formats::json::Value &request_json,
    userver::server::request::RequestContext &) const {
  auto &http_response = request.GetHttpResponse();
  const auto request_data = ParseRequest(request_json);

  if (request_data.configs.IsEmpty() || request_data.service.empty()) {
    http_response.SetStatus(userver::server::http::HttpStatus::kBadRequest);
    return uservice_dynconf::utils::MakeError(
        "400", "Fields 'configs' and 'service' are required");
  }
  if (!ConsitstsOfIdsFromConfigs(request_data.kill_switches_enabled,
                                 request_data.configs) ||
      !ConsitstsOfIdsFromConfigs(request_data.kill_switches_disabled,
                                 request_data.configs)) {
    http_response.SetStatus(userver::server::http::HttpStatus::kBadRequest);
    return uservice_dynconf::utils::MakeError(
        "400", "Fields 'kill_switches_enabled' and 'kill_switches_disabled' "
               "must consist of ids from 'configs' field");
  }
  if (HasIntersection(request_data.kill_switches_enabled,
                      request_data.kill_switches_disabled)) {
    http_response.SetStatus(userver::server::http::HttpStatus::kBadRequest);
    return uservice_dynconf::utils::MakeError(
        "400", "Ids in 'kill_switches_enabled' and 'kill_switches_disabled' "
               "must not overlap");
  }

  const auto config_mode_map = MakeConfigModeMap(
      request_data.configs, request_data.kill_switches_enabled,
      request_data.kill_switches_disabled);
  cluster_->Execute(userver::storages::postgres::ClusterHostType::kMaster,
                    uservice_dynconf::sql::kInsertConfigValue.data(),
                    request_data.service, request_data.configs,
                    config_mode_map);

  http_response.SetStatus(userver::server::http::HttpStatus::kNoContent);

  return {};
}

} // namespace uservice_dynconf::handlers::admin_v1_configs::post
