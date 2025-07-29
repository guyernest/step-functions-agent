import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListStateMachineVersionsCommand, se_ListStateMachineVersionsCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class ListStateMachineVersionsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "ListStateMachineVersions", {})
    .n("SFNClient", "ListStateMachineVersionsCommand")
    .f(void 0, void 0)
    .ser(se_ListStateMachineVersionsCommand)
    .de(de_ListStateMachineVersionsCommand)
    .build() {
}
