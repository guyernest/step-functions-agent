import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { GetExecutionHistoryOutputFilterSensitiveLog, } from "../models/models_0";
import { de_GetExecutionHistoryCommand, se_GetExecutionHistoryCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class GetExecutionHistoryCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "GetExecutionHistory", {})
    .n("SFNClient", "GetExecutionHistoryCommand")
    .f(void 0, GetExecutionHistoryOutputFilterSensitiveLog)
    .ser(se_GetExecutionHistoryCommand)
    .de(de_GetExecutionHistoryCommand)
    .build() {
}
