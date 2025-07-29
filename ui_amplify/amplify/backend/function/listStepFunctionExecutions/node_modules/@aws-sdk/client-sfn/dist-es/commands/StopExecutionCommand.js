import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { StopExecutionInputFilterSensitiveLog } from "../models/models_0";
import { de_StopExecutionCommand, se_StopExecutionCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class StopExecutionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "StopExecution", {})
    .n("SFNClient", "StopExecutionCommand")
    .f(StopExecutionInputFilterSensitiveLog, void 0)
    .ser(se_StopExecutionCommand)
    .de(de_StopExecutionCommand)
    .build() {
}
