import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { SendTaskFailureInputFilterSensitiveLog, } from "../models/models_0";
import { de_SendTaskFailureCommand, se_SendTaskFailureCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class SendTaskFailureCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "SendTaskFailure", {})
    .n("SFNClient", "SendTaskFailureCommand")
    .f(SendTaskFailureInputFilterSensitiveLog, void 0)
    .ser(se_SendTaskFailureCommand)
    .de(de_SendTaskFailureCommand)
    .build() {
}
