import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { DescribeStateMachineAliasOutputFilterSensitiveLog, } from "../models/models_0";
import { de_DescribeStateMachineAliasCommand, se_DescribeStateMachineAliasCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeStateMachineAliasCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeStateMachineAlias", {})
    .n("SFNClient", "DescribeStateMachineAliasCommand")
    .f(void 0, DescribeStateMachineAliasOutputFilterSensitiveLog)
    .ser(se_DescribeStateMachineAliasCommand)
    .de(de_DescribeStateMachineAliasCommand)
    .build() {
}
