import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { DescribeStateMachineForExecutionOutputFilterSensitiveLog, } from "../models/models_0";
import { de_DescribeStateMachineForExecutionCommand, se_DescribeStateMachineForExecutionCommand, } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeStateMachineForExecutionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeStateMachineForExecution", {})
    .n("SFNClient", "DescribeStateMachineForExecutionCommand")
    .f(void 0, DescribeStateMachineForExecutionOutputFilterSensitiveLog)
    .ser(se_DescribeStateMachineForExecutionCommand)
    .de(de_DescribeStateMachineForExecutionCommand)
    .build() {
}
