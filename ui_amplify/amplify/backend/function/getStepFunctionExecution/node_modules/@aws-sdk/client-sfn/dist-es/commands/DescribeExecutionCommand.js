import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { DescribeExecutionOutputFilterSensitiveLog, } from "../models/models_0";
import { de_DescribeExecutionCommand, se_DescribeExecutionCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeExecutionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeExecution", {})
    .n("SFNClient", "DescribeExecutionCommand")
    .f(void 0, DescribeExecutionOutputFilterSensitiveLog)
    .ser(se_DescribeExecutionCommand)
    .de(de_DescribeExecutionCommand)
    .build() {
}
