// onnxruntime_register.cpp
#include "onnxruntime_register.h"
#include "ort_utils.h"

const char* c_MMDeployOpDomain = "mmdeploy";

#ifdef __cplusplus
extern "C" {
#endif

OrtStatus* ORT_API_CALL RegisterCustomOps(OrtSessionOptions* options, const OrtApiBase* api) {
    const OrtApi* kOrtApi = api->GetApi(ORT_API_VERSION);
    OrtStatus* status = nullptr;

    for (auto& _op_list_pair : mmdeploy::get_mmdeploy_custom_ops()) {
        OrtCustomOpDomain* domain = nullptr;

        if (auto status_create = kOrtApi->CreateCustomOpDomain(_op_list_pair.first.c_str(), &domain)) {
            return status_create;
        }

        auto& _op_list = _op_list_pair.second;
        for (auto& _op : _op_list) {
            if (auto status_add = kOrtApi->CustomOpDomain_Add(domain, _op)) {
                return status_add;
            }
        }

        status = kOrtApi->AddCustomOpDomain(options, domain);
    }

    return status;
}

#ifdef __cplusplus
}
#endif
