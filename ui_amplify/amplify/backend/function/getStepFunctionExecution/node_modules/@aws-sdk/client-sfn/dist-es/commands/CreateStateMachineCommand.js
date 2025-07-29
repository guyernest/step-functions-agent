import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { CreateStateMachineInputFilterSensitiveLog, } from "../models/models_0";
import { de_CreateStateMachineCommand, se_CreateStateMachineCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class CreateStateMachineCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "CreateStateMachine", {})
    .n("SFNClient", "CreateStateMachineCommand")
    .f(CreateStateMachineInputFilterSensitiveLog, void 0)
    .ser(se_CreateStateMachineCommand)
    .de(de_CreateStateMachineCommand)
    .build() {
}
