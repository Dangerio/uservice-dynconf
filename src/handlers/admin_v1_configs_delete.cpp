#include <handlers/admin_v1_configs_delete.hpp>

#include <string>
#include <vector>

#include <userver/formats/json/value.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/postgres/cluster.hpp>
#include <userver/storages/postgres/component.hpp>

#include <docs/api/api.hpp>
#include <uservice_dynconf/sql_queries.hpp>

#include <utils/make_error.hpp>

namespace uservice_dynconf::handlers::admin_v1_configs_delete::post {

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
  auto &&request_data = request_json.As<AdminConfigsDeleteRequestBody>();
  std::vector<std::string> ids =
      request_data.ids.value_or(std::vector<std::string>({}));
  std::string service = request_data.service.value_or(std::string({}));

  auto &http_response = request.GetHttpResponse();
  if (ids.empty() || service.empty()) {
    http_response.SetStatus(userver::server::http::HttpStatus::kBadRequest);
    return uservice_dynconf::utils::MakeError(
        "400", "Fields 'ids' and 'service' are required");
  }

  cluster_->Execute(userver::storages::postgres::ClusterHostType::kMaster,
                    uservice_dynconf::sql::kDeleteConfigValues, service, ids);

  http_response.SetStatus(userver::server::http::HttpStatus::kNoContent);
  return {};
}

} // namespace uservice_dynconf::handlers::admin_v1_configs_delete::post
