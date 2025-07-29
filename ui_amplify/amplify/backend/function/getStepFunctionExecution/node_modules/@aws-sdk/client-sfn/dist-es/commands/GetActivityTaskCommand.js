import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { GetActivityTaskOutputFilterSensitiveLog, } from "../models/models_0";
import { de_GetActivityTaskCommand, se_GetActivityTaskCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class GetActivityTaskCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "GetActivityTask", {})
    .n("SFNClient", "GetActivityTaskCommand")
    .f(void 0, GetActivityTaskOutputFilterSensitiveLog)
    .ser(se_GetActivityTaskCommand)
    .de(de_GetActivityTaskCommand)
    .build() {
}
