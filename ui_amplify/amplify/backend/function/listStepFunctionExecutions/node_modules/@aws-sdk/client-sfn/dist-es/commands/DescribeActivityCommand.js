import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DescribeActivityCommand, se_DescribeActivityCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DescribeActivityCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DescribeActivity", {})
    .n("SFNClient", "DescribeActivityCommand")
    .f(void 0, void 0)
    .ser(se_DescribeActivityCommand)
    .de(de_DescribeActivityCommand)
    .build() {
}
