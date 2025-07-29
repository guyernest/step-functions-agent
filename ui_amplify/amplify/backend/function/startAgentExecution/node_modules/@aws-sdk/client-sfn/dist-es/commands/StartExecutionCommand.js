import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { StartExecutionInputFilterSensitiveLog } from "../models/models_0";
import { de_StartExecutionCommand, se_StartExecutionCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class StartExecutionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "StartExecution", {})
    .n("SFNClient", "StartExecutionCommand")
    .f(StartExecutionInputFilterSensitiveLog, void 0)
    .ser(se_StartExecutionCommand)
    .de(de_StartExecutionCommand)
    .build() {
}
