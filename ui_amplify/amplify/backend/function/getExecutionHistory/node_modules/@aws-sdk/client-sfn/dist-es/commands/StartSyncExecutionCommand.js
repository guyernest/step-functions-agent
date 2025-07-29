import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { StartSyncExecutionInputFilterSensitiveLog, StartSyncExecutionOutputFilterSensitiveLog, } from "../models/models_0";
import { de_StartSyncExecutionCommand, se_StartSyncExecutionCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class StartSyncExecutionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "StartSyncExecution", {})
    .n("SFNClient", "StartSyncExecutionCommand")
    .f(StartSyncExecutionInputFilterSensitiveLog, StartSyncExecutionOutputFilterSensitiveLog)
    .ser(se_StartSyncExecutionCommand)
    .de(de_StartSyncExecutionCommand)
    .build() {
}
