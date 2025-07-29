import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListStateMachinesCommand, se_ListStateMachinesCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class ListStateMachinesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "ListStateMachines", {})
    .n("SFNClient", "ListStateMachinesCommand")
    .f(void 0, void 0)
    .ser(se_ListStateMachinesCommand)
    .de(de_ListStateMachinesCommand)
    .build() {
}
