import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListMapRunsCommand, se_ListMapRunsCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class ListMapRunsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "ListMapRuns", {})
    .n("SFNClient", "ListMapRunsCommand")
    .f(void 0, void 0)
    .ser(se_ListMapRunsCommand)
    .de(de_ListMapRunsCommand)
    .build() {
}
