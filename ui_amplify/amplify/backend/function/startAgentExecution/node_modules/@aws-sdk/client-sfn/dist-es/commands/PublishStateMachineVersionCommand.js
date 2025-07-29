import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { PublishStateMachineVersionInputFilterSensitiveLog, } from "../models/models_0";
import { de_PublishStateMachineVersionCommand, se_PublishStateMachineVersionCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class PublishStateMachineVersionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "PublishStateMachineVersion", {})
    .n("SFNClient", "PublishStateMachineVersionCommand")
    .f(PublishStateMachineVersionInputFilterSensitiveLog, void 0)
    .ser(se_PublishStateMachineVersionCommand)
    .de(de_PublishStateMachineVersionCommand)
    .build() {
}
