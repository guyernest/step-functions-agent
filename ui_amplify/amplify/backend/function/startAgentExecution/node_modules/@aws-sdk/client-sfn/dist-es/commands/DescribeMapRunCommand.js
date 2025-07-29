import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DescribeMapRunCommand, se_DescribeMapRunCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeMapRunCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeMapRun", {})
    .n("SFNClient", "DescribeMapRunCommand")
    .f(void 0, void 0)
    .ser(se_DescribeMapRunCommand)
    .de(de_DescribeMapRunCommand)
    .build() {
}
