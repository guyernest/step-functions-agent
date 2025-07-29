import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { SendTaskSuccessInputFilterSensitiveLog, } from "../models/models_0";
import { de_SendTaskSuccessCommand, se_SendTaskSuccessCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class SendTaskSuccessCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "SendTaskSuccess", {})
    .n("SFNClient", "SendTaskSuccessCommand")
    .f(SendTaskSuccessInputFilterSensitiveLog, void 0)
    .ser(se_SendTaskSuccessCommand)
    .de(de_SendTaskSuccessCommand)
    .build() {
}
