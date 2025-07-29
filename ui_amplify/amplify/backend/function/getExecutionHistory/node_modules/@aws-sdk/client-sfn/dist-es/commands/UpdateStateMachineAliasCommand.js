import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { UpdateStateMachineAliasInputFilterSensitiveLog, } from "../models/models_0";
import { de_UpdateStateMachineAliasCommand, se_UpdateStateMachineAliasCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class UpdateStateMachineAliasCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "UpdateStateMachineAlias", {})
    .n("SFNClient", "UpdateStateMachineAliasCommand")
    .f(UpdateStateMachineAliasInputFilterSensitiveLog, void 0)
    .ser(se_UpdateStateMachineAliasCommand)
    .de(de_UpdateStateMachineAliasCommand)
    .build() {
}
