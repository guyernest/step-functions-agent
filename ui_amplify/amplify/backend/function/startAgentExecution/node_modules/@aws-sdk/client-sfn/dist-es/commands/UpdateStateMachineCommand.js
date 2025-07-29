import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { UpdateStateMachineInputFilterSensitiveLog, } from "../models/models_0";
import { de_UpdateStateMachineCommand, se_UpdateStateMachineCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class UpdateStateMachineCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "UpdateStateMachine", {})
    .n("SFNClient", "UpdateStateMachineCommand")
    .f(UpdateStateMachineInputFilterSensitiveLog, void 0)
    .ser(se_UpdateStateMachineCommand)
    .de(de_UpdateStateMachineCommand)
    .build() {
}
