import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { DescribeStateMachineOutputFilterSensitiveLog, } from "../models/models_0";
import { de_DescribeStateMachineCommand, se_DescribeStateMachineCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeStateMachineCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeStateMachine", {})
    .n("SFNClient", "DescribeStateMachineCommand")
    .f(void 0, DescribeStateMachineOutputFilterSensitiveLog)
    .ser(se_DescribeStateMachineCommand)
    .de(de_DescribeStateMachineCommand)
    .build() {
}
