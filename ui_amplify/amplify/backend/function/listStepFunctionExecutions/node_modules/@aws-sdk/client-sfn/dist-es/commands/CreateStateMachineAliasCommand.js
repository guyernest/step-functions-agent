import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { CreateStateMachineAliasInputFilterSensitiveLog, } from "../models/models_0";
import { de_CreateStateMachineAliasCommand, se_CreateStateMachineAliasCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class CreateStateMachineAliasCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "CreateStateMachineAlias", {})
    .n("SFNClient", "CreateStateMachineAliasCommand")
    .f(CreateStateMachineAliasInputFilterSensitiveLog, void 0)
    .ser(se_CreateStateMachineAliasCommand)
    .de(de_CreateStateMachineAliasCommand)
    .build() {
}
